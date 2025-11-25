"""
Scanner.py - Shadow Flow Detection & Whale Tracking
MIMIC V3.1 HARDENED

Implements:
- Shadow ID tracking with PERSISTENT storage (survives reboots)
- Volume spike detection
- Resolution arbitrage detection
- Order flow imbalance analysis
- Whale fingerprinting with improved heuristics
"""

import asyncio
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum

from .kalshi_client import KalshiClient

# Avoid circular import
if TYPE_CHECKING:
    from .persistence import MimicDB


class StrategyType(Enum):
    ARBITRAGE = "ARBITRAGE"          # Resolution snipers (fast lane)
    INFORMATIONAL = "INFORMATIONAL"  # News-driven whales (slow lane)
    MARKET_MAKER = "MARKET_MAKER"    # Structural/passive
    UNKNOWN = "UNKNOWN"


@dataclass
class WhaleProfile:
    """Tracks historical performance of a shadow ID (in-memory cache)"""
    shadow_id: str
    first_seen: datetime = field(default_factory=datetime.utcnow)
    total_trades: int = 0
    winning_trades: int = 0
    total_volume: float = 0.0
    total_pnl: float = 0.0
    avg_size: float = 0.0
    preferred_side: str = "neutral"
    strategy_signals: Dict[str, int] = field(default_factory=dict)

    @property
    def win_rate(self) -> float:
        return self.winning_trades / self.total_trades if self.total_trades > 0 else 0.5

    @property
    def edge_score(self) -> float:
        """Composite score of whale quality"""
        if self.total_trades < 5:
            return 0.5
        wr = self.win_rate
        vol_factor = min(1.0, self.total_volume / 100000)
        return (wr * 0.7) + (vol_factor * 0.3)


@dataclass
class WhaleSignal:
    """Detected whale activity signal"""
    shadow_id: str
    ticker: str
    event_ticker: str
    side: str
    price: float
    volume: float
    strategy_type: StrategyType
    confidence: float
    timestamp: datetime
    raw_market_data: Dict
    resolution_proximity: Optional[float] = None
    order_flow_imbalance: float = 0.0
    raw_hash: str = ""  # Original hash before friendly ID mapping


class ShadowScanner:
    """
    Whale detection and tracking system with PERSISTENCE.

    Detection Methods:
    1. Volume Spike: Single trade > threshold
    2. Resolution Proximity: Trades near settlement with high confidence
    3. Order Flow Imbalance: One-sided volume surge
    4. Shadow Pattern: Known whale fingerprint activity

    HARDENED Features:
    - SQLite persistence for Shadow IDs (survives reboots)
    - Improved fingerprinting with time-based clustering
    - Cross-market correlation tracking
    """

    def __init__(
        self,
        client: KalshiClient = None,
        db: 'MimicDB' = None,
        volume_threshold: float = 500.0,
        resolution_window_hours: float = 2.0,
        imbalance_threshold: float = 0.7,
        logger: logging.Logger = None
    ):
        self.client = client
        self.db = db  # Persistence layer
        self.volume_threshold = volume_threshold
        self.resolution_window_hours = resolution_window_hours
        self.imbalance_threshold = imbalance_threshold
        self.logger = logger or logging.getLogger(__name__)

        # In-memory cache (synced with DB)
        self.whale_profiles: Dict[str, WhaleProfile] = {}
        self.recent_trades: Dict[str, List[Dict]] = defaultdict(list)

        # Market state cache
        self.market_cache: Dict[str, Dict] = {}
        self.orderbook_cache: Dict[str, Dict] = {}

        # Time-based clustering for better fingerprinting
        self._trade_clusters: Dict[str, List[Tuple[datetime, Dict]]] = defaultdict(list)
        self._cluster_window_seconds = 60  # Group trades within 60s

        # Signal queue for async processing
        self.signal_queue: asyncio.Queue = asyncio.Queue()

        # Statistics
        self.stats = {
            "trades_analyzed": 0,
            "signals_generated": 0,
            "arb_signals": 0,
            "info_signals": 0,
            "unique_whales": 0
        }

    def _generate_shadow_hash(self, trade_data: Dict) -> str:
        """
        Generate raw hash fingerprint for trade origin.

        Improved heuristics:
        - Size bucket (10s)
        - Price bucket (5s)
        - Side
        - Time bucket (hour of day)
        """
        now = datetime.utcnow()

        features = [
            str(trade_data.get("count", 0) // 10 * 10),  # Size bucket
            str(int(trade_data.get("yes_price", 50) // 5 * 5)),  # Price bucket
            trade_data.get("taker_side", "unknown"),
            str(now.hour // 4),  # Time-of-day bucket (6 buckets)
        ]

        feature_str = "|".join(features)
        return hashlib.md5(feature_str.encode()).hexdigest()

    def _resolve_shadow_id(self, raw_hash: str, volume: float) -> str:
        """
        Resolve raw hash to persistent friendly ID.
        Uses database if available, otherwise in-memory.
        """
        if self.db:
            # Use persistent storage
            friendly_id = self.db.get_or_create_shadow_id(raw_hash, volume)
            return friendly_id
        else:
            # Fallback to in-memory
            return f"WHALE_{raw_hash[:8].upper()}"

    def _classify_strategy(
        self,
        trade: Dict,
        market: Dict,
        resolution_hours: Optional[float]
    ) -> Tuple[StrategyType, float]:
        """
        Classify the likely strategy behind a trade.

        Enhanced with:
        - Better resolution arb detection
        - Volume-weighted confidence
        """
        price = trade.get("yes_price", 50) / 100.0
        count = trade.get("count", 0)
        volume = count * price

        # ARBITRAGE: Near resolution with extreme prices
        if resolution_hours is not None and resolution_hours < self.resolution_window_hours:
            if price > 0.95 or price < 0.05:
                # Very high confidence arb
                confidence = 0.95 if volume > self.volume_threshold * 3 else 0.85
                return StrategyType.ARBITRAGE, confidence

            if price > 0.85 or price < 0.15:
                return StrategyType.ARBITRAGE, 0.75

            # Even moderate prices near resolution might be arb
            if price > 0.75 or price < 0.25:
                return StrategyType.ARBITRAGE, 0.60

        # INFORMATIONAL: Large size at mid-range prices
        if volume > self.volume_threshold * 3 and 0.30 < price < 0.70:
            return StrategyType.INFORMATIONAL, 0.85

        if volume > self.volume_threshold * 2 and 0.25 < price < 0.75:
            return StrategyType.INFORMATIONAL, 0.75

        if volume > self.volume_threshold:
            return StrategyType.INFORMATIONAL, 0.60

        # MARKET_MAKER: Two-sided, moderate size
        # (Would need order book analysis to detect properly)

        return StrategyType.UNKNOWN, 0.30

    def _calculate_resolution_proximity(self, market: Dict) -> Optional[float]:
        """Calculate hours until market settlement"""
        close_time_str = market.get("close_time") or market.get("expected_expiration_time")
        if not close_time_str:
            return None

        try:
            if isinstance(close_time_str, str):
                close_time = datetime.fromisoformat(close_time_str.replace('Z', '+00:00'))
            else:
                close_time = close_time_str

            now = datetime.now(close_time.tzinfo) if close_time.tzinfo else datetime.utcnow()
            delta = close_time - now
            return max(0, delta.total_seconds() / 3600.0)

        except Exception as e:
            self.logger.debug(f"Could not parse close time: {e}")
            return None

    def _calculate_order_flow_imbalance(self, ticker: str) -> float:
        """
        Calculate order flow imbalance from recent trades.
        Returns: -1 (all NO) to +1 (all YES)
        """
        trades = self.recent_trades.get(ticker, [])
        if not trades:
            return 0.0

        recent = trades[-50:]

        yes_volume = sum(t.get("count", 0) for t in recent if t.get("taker_side") == "yes")
        no_volume = sum(t.get("count", 0) for t in recent if t.get("taker_side") == "no")

        total = yes_volume + no_volume
        if total == 0:
            return 0.0

        return (yes_volume - no_volume) / total

    def _calculate_volume_zscore(self, volume: float, ticker: str) -> float:
        """Calculate how unusual this volume is compared to recent trades"""
        trades = self.recent_trades.get(ticker, [])
        if len(trades) < 10:
            return 0.0

        volumes = [t.get("count", 0) * (t.get("yes_price", 50) / 100.0) for t in trades[-50:]]
        if not volumes:
            return 0.0

        mean_vol = sum(volumes) / len(volumes)
        variance = sum((v - mean_vol) ** 2 for v in volumes) / len(volumes)
        std_vol = variance ** 0.5 if variance > 0 else 1.0

        return (volume - mean_vol) / std_vol if std_vol > 0 else 0.0

    async def analyze_trade(self, trade: Dict, market: Dict) -> Optional[WhaleSignal]:
        """
        Analyze a single trade for whale activity.

        HARDENED: Uses persistent Shadow IDs.
        """
        self.stats["trades_analyzed"] += 1

        ticker = market.get("ticker", "")
        price = trade.get("yes_price", 50) / 100.0
        count = trade.get("count", 0)
        volume = count * price

        # Store for flow analysis
        self.recent_trades[ticker].append(trade)
        if len(self.recent_trades[ticker]) > 100:
            self.recent_trades[ticker] = self.recent_trades[ticker][-100:]

        # Check volume threshold
        if volume < self.volume_threshold:
            return None

        # Generate raw hash
        raw_hash = self._generate_shadow_hash(trade)

        # Resolve to persistent friendly ID
        shadow_id = self._resolve_shadow_id(raw_hash, volume)

        # Get/create in-memory profile cache
        if shadow_id not in self.whale_profiles:
            self.whale_profiles[shadow_id] = WhaleProfile(shadow_id=shadow_id)
            self.stats["unique_whales"] += 1

            # Load from DB if available
            if self.db:
                db_stats = self.db.get_whale_stats(shadow_id)
                if db_stats:
                    profile = self.whale_profiles[shadow_id]
                    profile.total_trades = db_stats.get('total_trades', 0)
                    profile.winning_trades = db_stats.get('winning_trades', 0)
                    profile.total_volume = db_stats.get('total_volume', 0)
                    profile.total_pnl = db_stats.get('total_pnl', 0)

        profile = self.whale_profiles[shadow_id]

        # Calculate market proximity
        resolution_hours = self._calculate_resolution_proximity(market)

        # Classify strategy
        strategy_type, confidence = self._classify_strategy(trade, market, resolution_hours)

        # Calculate order flow
        imbalance = self._calculate_order_flow_imbalance(ticker)

        # Boost confidence if whale has good track record
        if profile.total_trades >= 10 and profile.win_rate > 0.60:
            confidence = min(0.95, confidence + 0.10)

        # Create signal
        signal = WhaleSignal(
            shadow_id=shadow_id,
            ticker=ticker,
            event_ticker=market.get("event_ticker", ""),
            side=trade.get("taker_side", "yes"),
            price=price,
            volume=volume,
            strategy_type=strategy_type,
            confidence=confidence,
            timestamp=datetime.utcnow(),
            raw_market_data=market,
            resolution_proximity=resolution_hours,
            order_flow_imbalance=imbalance,
            raw_hash=raw_hash
        )

        # Update in-memory profile
        profile.total_trades += 1
        profile.total_volume += volume
        profile.avg_size = profile.total_volume / profile.total_trades

        strategy_key = strategy_type.value
        profile.strategy_signals[strategy_key] = profile.strategy_signals.get(strategy_key, 0) + 1

        # Update stats
        self.stats["signals_generated"] += 1
        if strategy_type == StrategyType.ARBITRAGE:
            self.stats["arb_signals"] += 1
        elif strategy_type == StrategyType.INFORMATIONAL:
            self.stats["info_signals"] += 1

        self.logger.info(
            f"WHALE SIGNAL: {shadow_id} | {ticker} | "
            f"{signal.side.upper()} @ {price:.2f} | "
            f"${volume:.0f} | {strategy_type.value} | "
            f"Conf: {confidence:.0%}"
        )

        return signal

    async def poll_market_stream(self) -> Optional[WhaleSignal]:
        """Poll for new whale signals from queue."""
        try:
            signal = self.signal_queue.get_nowait()
            return signal
        except asyncio.QueueEmpty:
            return None

    async def scan_markets(self, tickers: List[str] = None) -> List[WhaleSignal]:
        """Scan multiple markets for whale activity via REST API."""
        if not self.client:
            self.logger.warning("No client configured for scanning")
            return []

        signals = []

        if not tickers:
            markets_response = await self.client.get_markets(status="open", limit=50)
            tickers = [m["ticker"] for m in markets_response.get("markets", [])]

        for ticker in tickers:
            try:
                market = await self.client.get_market(ticker)
                market_data = market.get("market", {})

                trades_response = await self.client.get_trades(ticker, limit=20)
                trades = trades_response.get("trades", [])

                for trade in trades:
                    signal = await self.analyze_trade(trade, market_data)
                    if signal:
                        signals.append(signal)

            except Exception as e:
                self.logger.error(f"Error scanning {ticker}: {e}")

        return signals

    def setup_websocket_handlers(self, client: KalshiClient):
        """Register WebSocket handlers for real-time scanning"""

        @client.on_message("trade")
        async def handle_trade(data: Dict):
            ticker = data.get("market_ticker")
            if not ticker:
                return

            if ticker not in self.market_cache:
                try:
                    market = await client.get_market(ticker)
                    self.market_cache[ticker] = market.get("market", {})
                except Exception as e:
                    self.logger.error(f"Failed to fetch market {ticker}: {e}")
                    return

            market = self.market_cache[ticker]
            signal = await self.analyze_trade(data, market)

            if signal:
                await self.signal_queue.put(signal)

        @client.on_message("orderbook_delta")
        async def handle_orderbook(data: Dict):
            ticker = data.get("market_ticker")
            if ticker:
                self.orderbook_cache[ticker] = data

    def update_whale_outcome(self, shadow_id: str, is_win: bool, pnl: float, strategy_type: str = None):
        """
        Update whale profile with trade outcome.
        HARDENED: Persists to database.
        """
        # Update in-memory
        if shadow_id in self.whale_profiles:
            profile = self.whale_profiles[shadow_id]
            if is_win:
                profile.winning_trades += 1
            profile.total_pnl += pnl

            self.logger.debug(
                f"Updated {shadow_id}: WR={profile.win_rate:.2%}, PnL=${profile.total_pnl:.2f}"
            )

        # Persist to database
        if self.db:
            volume = self.whale_profiles.get(shadow_id, WhaleProfile(shadow_id)).avg_size
            self.db.update_whale_stats(shadow_id, volume, is_win, pnl, strategy_type)

    def get_whale_stats(self, shadow_id: str) -> Optional[Dict]:
        """Get statistics for a specific whale"""
        # Try database first
        if self.db:
            db_stats = self.db.get_whale_stats(shadow_id)
            if db_stats:
                return db_stats

        # Fall back to in-memory
        if shadow_id not in self.whale_profiles:
            return None

        profile = self.whale_profiles[shadow_id]
        return {
            "shadow_id": shadow_id,
            "win_rate": profile.win_rate,
            "edge_score": profile.edge_score,
            "total_trades": profile.total_trades,
            "total_volume": profile.total_volume,
            "total_pnl": profile.total_pnl,
            "avg_size": profile.avg_size,
            "first_seen": profile.first_seen.isoformat(),
            "strategy_distribution": profile.strategy_signals
        }

    def get_top_whales(self, n: int = 10) -> List[Dict]:
        """Get top performing whales"""
        if self.db:
            return self.db.get_top_whales(limit=n)

        sorted_whales = sorted(
            self.whale_profiles.values(),
            key=lambda p: p.edge_score,
            reverse=True
        )
        return [self.get_whale_stats(w.shadow_id) for w in sorted_whales[:n]]

    def get_stats(self) -> Dict:
        """Get scanner statistics"""
        return {
            **self.stats,
            "cached_markets": len(self.market_cache),
            "tracked_whales": len(self.whale_profiles),
            "db_connected": self.db is not None
        }
