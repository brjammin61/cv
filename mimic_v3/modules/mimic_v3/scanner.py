"""
Scanner.py - Shadow Flow Detection & Whale Tracking
MIMIC V3.1 - Production Ready

Implements:
- Shadow ID tracking (whale fingerprinting)
- Volume spike detection
- Resolution arbitrage detection
- Order flow imbalance analysis
"""

import asyncio
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum

from .kalshi_client import KalshiClient


class StrategyType(Enum):
    ARBITRAGE = "ARBITRAGE"          # Resolution snipers (fast lane)
    INFORMATIONAL = "INFORMATIONAL"  # News-driven whales (slow lane)
    MARKET_MAKER = "MARKET_MAKER"    # Structural/passive
    UNKNOWN = "UNKNOWN"


@dataclass
class WhaleProfile:
    """Tracks historical performance of a shadow ID"""
    shadow_id: str
    first_seen: datetime = field(default_factory=datetime.utcnow)
    total_trades: int = 0
    winning_trades: int = 0
    total_volume: float = 0.0
    total_pnl: float = 0.0
    avg_size: float = 0.0
    preferred_side: str = "neutral"  # yes, no, neutral
    strategy_signals: Dict[str, int] = field(default_factory=dict)

    @property
    def win_rate(self) -> float:
        return self.winning_trades / self.total_trades if self.total_trades > 0 else 0.5

    @property
    def edge_score(self) -> float:
        """Composite score of whale quality"""
        if self.total_trades < 5:
            return 0.5  # Not enough data
        wr = self.win_rate
        vol_factor = min(1.0, self.total_volume / 100000)  # Scale by volume
        return (wr * 0.7) + (vol_factor * 0.3)


@dataclass
class WhaleSignal:
    """Detected whale activity signal"""
    shadow_id: str
    ticker: str
    event_ticker: str
    side: str  # "yes" or "no"
    price: float  # 0-1
    volume: float  # Dollar amount
    strategy_type: StrategyType
    confidence: float  # 0-1
    timestamp: datetime
    raw_market_data: Dict
    resolution_proximity: Optional[float] = None  # Hours until settlement
    order_flow_imbalance: float = 0.0  # -1 to 1


class ShadowScanner:
    """
    Whale detection and tracking system.

    Detection Methods:
    1. Volume Spike: Single trade > threshold (default $1000)
    2. Resolution Proximity: Trades near settlement with high confidence
    3. Order Flow Imbalance: One-sided volume surge
    4. Shadow Pattern: Known whale fingerprint activity
    """

    def __init__(
        self,
        client: KalshiClient = None,
        volume_threshold: float = 1000.0,
        resolution_window_hours: float = 2.0,
        imbalance_threshold: float = 0.7,
        logger: logging.Logger = None
    ):
        self.client = client
        self.volume_threshold = volume_threshold
        self.resolution_window_hours = resolution_window_hours
        self.imbalance_threshold = imbalance_threshold
        self.logger = logger or logging.getLogger(__name__)

        # Shadow ID tracking
        self.whale_profiles: Dict[str, WhaleProfile] = {}
        self.recent_trades: Dict[str, List[Dict]] = defaultdict(list)

        # Market state cache
        self.market_cache: Dict[str, Dict] = {}
        self.orderbook_cache: Dict[str, Dict] = {}

        # Signal queue for async processing
        self.signal_queue: asyncio.Queue = asyncio.Queue()

        # Statistics
        self.stats = {
            "trades_analyzed": 0,
            "signals_generated": 0,
            "arb_signals": 0,
            "info_signals": 0
        }

    def _generate_shadow_id(self, trade_data: Dict) -> str:
        """
        Generate fingerprint for trade origin.

        In production, this would use more sophisticated heuristics:
        - Trade timing patterns
        - Size clustering
        - Price level preferences
        - Cross-market correlation

        For now, we use a hash of observable characteristics.
        """
        # Features that might identify a trader
        features = [
            str(trade_data.get("count", 0) // 10 * 10),  # Size bucket
            str(int(trade_data.get("yes_price", 50) // 5 * 5)),  # Price bucket
            trade_data.get("taker_side", "unknown"),
        ]

        # Create deterministic hash
        feature_str = "|".join(features)
        hash_obj = hashlib.md5(feature_str.encode())
        return f"WHALE_{hash_obj.hexdigest()[:8].upper()}"

    def _classify_strategy(
        self,
        trade: Dict,
        market: Dict,
        resolution_hours: Optional[float]
    ) -> Tuple[StrategyType, float]:
        """
        Classify the likely strategy behind a trade.

        Returns:
            (strategy_type, confidence)
        """
        price = trade.get("yes_price", 50) / 100.0
        volume = trade.get("count", 0) * price

        # ARBITRAGE: High confidence near resolution
        if resolution_hours is not None and resolution_hours < self.resolution_window_hours:
            # Extreme prices (>95% or <5%) near resolution = likely arb
            if price > 0.95 or price < 0.05:
                return StrategyType.ARBITRAGE, 0.9

            # High confidence prices near resolution
            if price > 0.85 or price < 0.15:
                return StrategyType.ARBITRAGE, 0.7

        # INFORMATIONAL: Large size at mid-range prices
        if volume > self.volume_threshold * 2 and 0.25 < price < 0.75:
            return StrategyType.INFORMATIONAL, 0.8

        # Default: Large volume = informational
        if volume > self.volume_threshold:
            return StrategyType.INFORMATIONAL, 0.6

        return StrategyType.UNKNOWN, 0.3

    def _calculate_resolution_proximity(self, market: Dict) -> Optional[float]:
        """Calculate hours until market settlement"""
        close_time_str = market.get("close_time") or market.get("expected_expiration_time")
        if not close_time_str:
            return None

        try:
            # Parse ISO format
            if isinstance(close_time_str, str):
                close_time = datetime.fromisoformat(close_time_str.replace('Z', '+00:00'))
            else:
                close_time = close_time_str

            now = datetime.now(close_time.tzinfo) if close_time.tzinfo else datetime.utcnow()
            delta = close_time - now
            return delta.total_seconds() / 3600.0

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

        # Look at last N trades
        recent = trades[-50:]

        yes_volume = sum(t.get("count", 0) for t in recent if t.get("taker_side") == "yes")
        no_volume = sum(t.get("count", 0) for t in recent if t.get("taker_side") == "no")

        total = yes_volume + no_volume
        if total == 0:
            return 0.0

        return (yes_volume - no_volume) / total

    async def analyze_trade(self, trade: Dict, market: Dict) -> Optional[WhaleSignal]:
        """
        Analyze a single trade for whale activity.

        Args:
            trade: Trade data from WebSocket or REST API
            market: Market metadata

        Returns:
            WhaleSignal if whale activity detected, None otherwise
        """
        self.stats["trades_analyzed"] += 1

        ticker = market.get("ticker", "")
        price = trade.get("yes_price", 50) / 100.0
        count = trade.get("count", 0)
        volume = count * price  # Approximate dollar volume

        # Store for flow analysis
        self.recent_trades[ticker].append(trade)
        # Keep only last 100 trades per market
        if len(self.recent_trades[ticker]) > 100:
            self.recent_trades[ticker] = self.recent_trades[ticker][-100:]

        # Check volume threshold
        if volume < self.volume_threshold:
            return None

        # Generate shadow ID
        shadow_id = self._generate_shadow_id(trade)

        # Get/create whale profile
        if shadow_id not in self.whale_profiles:
            self.whale_profiles[shadow_id] = WhaleProfile(shadow_id=shadow_id)

        profile = self.whale_profiles[shadow_id]

        # Calculate market proximity
        resolution_hours = self._calculate_resolution_proximity(market)

        # Classify strategy
        strategy_type, confidence = self._classify_strategy(trade, market, resolution_hours)

        # Calculate order flow
        imbalance = self._calculate_order_flow_imbalance(ticker)

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
            order_flow_imbalance=imbalance
        )

        # Update profile
        profile.total_trades += 1
        profile.total_volume += volume
        profile.avg_size = profile.total_volume / profile.total_trades

        # Track strategy preferences
        strategy_key = strategy_type.value
        profile.strategy_signals[strategy_key] = profile.strategy_signals.get(strategy_key, 0) + 1

        self.stats["signals_generated"] += 1
        if strategy_type == StrategyType.ARBITRAGE:
            self.stats["arb_signals"] += 1
        elif strategy_type == StrategyType.INFORMATIONAL:
            self.stats["info_signals"] += 1

        self.logger.info(
            f"🐋 WHALE SIGNAL: {shadow_id} | {ticker} | "
            f"{signal.side.upper()} @ {price:.2f} | "
            f"${volume:.0f} | {strategy_type.value}"
        )

        return signal

    async def poll_market_stream(self) -> Optional[WhaleSignal]:
        """
        Poll for new whale signals.
        Called by the main event loop.
        """
        try:
            # Non-blocking check for queued signals
            signal = self.signal_queue.get_nowait()
            return signal
        except asyncio.QueueEmpty:
            return None

    async def scan_markets(self, tickers: List[str] = None) -> List[WhaleSignal]:
        """
        Scan multiple markets for whale activity.
        Uses REST API polling (for when WebSocket isn't available).
        """
        if not self.client:
            self.logger.warning("No client configured for scanning")
            return []

        signals = []

        # Get active markets if no tickers specified
        if not tickers:
            markets_response = await self.client.get_markets(status="open", limit=50)
            tickers = [m["ticker"] for m in markets_response.get("markets", [])]

        for ticker in tickers:
            try:
                # Get market info
                market = await self.client.get_market(ticker)
                market_data = market.get("market", {})

                # Get recent trades
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
            """Process incoming trade from WebSocket"""
            ticker = data.get("market_ticker")
            if not ticker:
                return

            # Get cached market data or fetch
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
            """Track orderbook for imbalance detection"""
            ticker = data.get("market_ticker")
            if ticker:
                self.orderbook_cache[ticker] = data

    def update_whale_outcome(self, shadow_id: str, is_win: bool, pnl: float):
        """
        Update whale profile with trade outcome.
        Called after settlement.
        """
        if shadow_id not in self.whale_profiles:
            return

        profile = self.whale_profiles[shadow_id]
        if is_win:
            profile.winning_trades += 1
        profile.total_pnl += pnl

        self.logger.debug(
            f"Updated {shadow_id}: WR={profile.win_rate:.2%}, PnL=${profile.total_pnl:.2f}"
        )

    def get_whale_stats(self, shadow_id: str) -> Optional[Dict]:
        """Get statistics for a specific whale"""
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
        """Get top performing whales by edge score"""
        sorted_whales = sorted(
            self.whale_profiles.values(),
            key=lambda p: p.edge_score,
            reverse=True
        )
        return [self.get_whale_stats(w.shadow_id) for w in sorted_whales[:n]]
