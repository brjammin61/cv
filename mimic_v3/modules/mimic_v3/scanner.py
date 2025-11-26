"""
Scanner.py - Shadow Flow Detection & Whale Tracking
MIMIC V3.1 HARDENED - REAL API POLLING VERSION

Implements:
- REAL Kalshi API polling for whale detection
- Shadow ID tracking with PERSISTENT storage (survives reboots)
- Volume spike detection
- No more fake/mock data generation
"""

import asyncio
import hashlib
import aiohttp
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set, TYPE_CHECKING
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum

# Avoid circular import
if TYPE_CHECKING:
    from .persistence import MimicDB


# Kalshi API URL - Production
KALSHI_API_URL = os.getenv("KALSHI_API_URL", "https://trading-api.kalshi.com/trade-api/v2")


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
    raw_hash: str = ""


class ShadowScanner:
    """
    Whale detection and tracking system with REAL API POLLING.

    FIXED VERSION:
    - Polls Kalshi REST API directly (no WebSocket auth issues)
    - Only generates signals from REAL trades
    - Persistent Shadow IDs via SQLite
    - No mock/fake data generation
    """

    def __init__(
        self,
        client=None,
        db: 'MimicDB' = None,
        volume_threshold: float = 500.0,
        resolution_window_hours: float = 2.0,
        imbalance_threshold: float = 0.7,
        logger: logging.Logger = None
    ):
        self.client = client
        self.db = db
        self.volume_threshold = volume_threshold
        self.resolution_window_hours = resolution_window_hours
        self.imbalance_threshold = imbalance_threshold
        self.logger = logger or logging.getLogger(__name__)

        # HTTP session for direct API calls
        self._session: Optional[aiohttp.ClientSession] = None

        # In-memory caches
        self.whale_profiles: Dict[str, WhaleProfile] = {}
        self.shadow_profiles: Dict[str, Dict] = {}  # For dashboard
        self.recent_trades: Dict[str, List[Dict]] = defaultdict(list)

        # Target markets to scan
        self.target_markets: List[str] = []
        self._last_market_refresh: datetime = datetime.now() - timedelta(minutes=10)

        # Processed trade IDs to avoid duplicates
        self._processed_trades: Set[str] = set()

        # Limit processed trades memory (keep last 10000)
        self._max_processed_trades = 10000

        # Statistics
        self.stats = {
            "trades_analyzed": 0,
            "signals_generated": 0,
            "arb_signals": 0,
            "info_signals": 0,
            "unique_whales": 0,
            "api_calls": 0,
            "api_errors": 0
        }

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            )
        return self._session

    async def _update_target_markets(self):
        """Fetch top volume markets to scan"""
        try:
            session = await self._get_session()
            url = f"{KALSHI_API_URL}/markets?limit=50&status=active"

            self.stats["api_calls"] += 1

            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    markets = data.get("markets", [])

                    # Sort by volume and take top markets
                    self.target_markets = [m["ticker"] for m in markets[:30]]
                    self._last_market_refresh = datetime.now()

                    self.logger.info(f"🔭 SCANNER: Targeting {len(self.target_markets)} active markets")
                else:
                    self.stats["api_errors"] += 1
                    self.logger.error(f"Failed to fetch markets: HTTP {resp.status}")

        except Exception as e:
            self.stats["api_errors"] += 1
            self.logger.error(f"Error updating target markets: {e}")

    def _generate_shadow_hash(self, ticker: str, trade: Dict) -> str:
        """Generate fingerprint for trade origin"""
        # Use trade characteristics to create pseudo-identity
        count = trade.get("count", 0)
        price = trade.get("price", 50)
        side = trade.get("taker_side", "unknown")
        created = trade.get("created_time", "")

        features = f"{ticker}|{count // 10 * 10}|{price // 5 * 5}|{side}|{created[:13]}"
        return hashlib.sha256(features.encode()).hexdigest()

    def _resolve_shadow_id(self, raw_hash: str, volume: float) -> str:
        """Resolve raw hash to persistent friendly ID"""
        if self.db:
            return self.db.get_or_create_shadow_id(raw_hash, volume)
        return f"WHALE_{raw_hash[:8].upper()}"

    def _classify_strategy(self, price: float, volume: float) -> Tuple[StrategyType, float]:
        """Classify trade strategy based on price and volume"""
        price_decimal = price / 100.0 if price > 1 else price

        # High confidence trades near extremes = arbitrage
        if price_decimal > 0.90 or price_decimal < 0.10:
            return StrategyType.ARBITRAGE, 0.85

        if price_decimal > 0.80 or price_decimal < 0.20:
            return StrategyType.ARBITRAGE, 0.70

        # Large volume at mid-range = informational
        if volume > self.volume_threshold * 3 and 0.30 < price_decimal < 0.70:
            return StrategyType.INFORMATIONAL, 0.85

        if volume > self.volume_threshold:
            return StrategyType.INFORMATIONAL, 0.65

        return StrategyType.UNKNOWN, 0.40

    async def poll_market_stream(self) -> Optional[WhaleSignal]:
        """
        REAL MODE: Poll Kalshi API for actual whale trades.

        This replaces the fake signal generation with real API polling.
        Returns a signal only when a REAL large trade is detected.
        """
        # Refresh market list every 5 minutes
        if datetime.now() - self._last_market_refresh > timedelta(minutes=5) or not self.target_markets:
            await self._update_target_markets()

        if not self.target_markets:
            self.logger.debug("No target markets available")
            return None

        session = await self._get_session()

        # Scan top 10 most active markets per cycle
        markets_to_scan = self.target_markets[:10]

        for ticker in markets_to_scan:
            try:
                # Fetch recent trades for this market
                url = f"{KALSHI_API_URL}/markets/{ticker}/trades?limit=10"
                self.stats["api_calls"] += 1

                async with session.get(url) as resp:
                    if resp.status != 200:
                        continue

                    data = await resp.json()
                    trades = data.get("trades", [])

                    for trade in trades:
                        trade_id = trade.get("trade_id")

                        # Skip if already processed
                        if trade_id in self._processed_trades:
                            continue

                        # Calculate volume
                        count = trade.get("count", 0)
                        price = trade.get("price", 50)  # Cents
                        volume = count * (price / 100.0)

                        # Skip small trades
                        if volume < self.volume_threshold:
                            continue

                        # Mark as processed
                        self._processed_trades.add(trade_id)

                        # Clean up old processed trades
                        if len(self._processed_trades) > self._max_processed_trades:
                            # Remove oldest entries (convert to list, slice, back to set)
                            self._processed_trades = set(list(self._processed_trades)[-5000:])

                        self.stats["trades_analyzed"] += 1

                        # Generate shadow ID
                        raw_hash = self._generate_shadow_hash(ticker, trade)
                        shadow_id = self._resolve_shadow_id(raw_hash, volume)

                        # Classify strategy
                        strategy_type, confidence = self._classify_strategy(price, volume)

                        # Update stats
                        self.stats["signals_generated"] += 1
                        if strategy_type == StrategyType.ARBITRAGE:
                            self.stats["arb_signals"] += 1
                        else:
                            self.stats["info_signals"] += 1

                        # Update whale profile for dashboard
                        if shadow_id not in self.whale_profiles:
                            self.whale_profiles[shadow_id] = WhaleProfile(shadow_id=shadow_id)
                            self.stats["unique_whales"] += 1

                        profile = self.whale_profiles[shadow_id]
                        profile.total_trades += 1
                        profile.total_volume += volume

                        # Update shadow_profiles for dashboard
                        self.shadow_profiles[shadow_id] = {
                            "friendly_id": shadow_id,
                            "volume": profile.total_volume,
                            "win_rate": profile.win_rate,
                            "total_pnl": profile.total_pnl,
                            "confidence": confidence,
                            "last_ticker": ticker,
                            "last_side": trade.get("taker_side", "yes"),
                            "last_seen": datetime.utcnow().isoformat(),
                            "strategy_type": strategy_type.value
                        }

                        self.logger.info(
                            f"🐋 REAL WHALE SIGNAL: {shadow_id} | {ticker} | "
                            f"{trade.get('taker_side', 'yes').upper()} @ {price}c | "
                            f"${volume:.0f} | {strategy_type.value}"
                        )

                        # Return the signal
                        return WhaleSignal(
                            shadow_id=shadow_id,
                            ticker=ticker,
                            event_ticker=ticker.split("-")[0] if "-" in ticker else ticker,
                            side=trade.get("taker_side", "yes"),
                            price=price / 100.0,
                            volume=volume,
                            strategy_type=strategy_type,
                            confidence=confidence,
                            timestamp=datetime.utcnow(),
                            raw_market_data={"ticker": ticker, "title": ticker},
                            raw_hash=raw_hash
                        )

            except asyncio.TimeoutError:
                self.stats["api_errors"] += 1
                self.logger.debug(f"Timeout scanning {ticker}")
            except Exception as e:
                self.stats["api_errors"] += 1
                self.logger.error(f"Error scanning {ticker}: {e}")

        # No whale found in this cycle
        return None

    def update_whale_outcome(self, shadow_id: str, is_win: bool, pnl: float, strategy_type: str = None):
        """Update whale profile with trade outcome"""
        if shadow_id in self.whale_profiles:
            profile = self.whale_profiles[shadow_id]
            if is_win:
                profile.winning_trades += 1
            profile.total_pnl += pnl

            # Update shadow_profiles for dashboard
            if shadow_id in self.shadow_profiles:
                self.shadow_profiles[shadow_id]["win_rate"] = profile.win_rate
                self.shadow_profiles[shadow_id]["total_pnl"] = profile.total_pnl

        # Persist to database
        if self.db:
            volume = self.whale_profiles.get(shadow_id, WhaleProfile(shadow_id)).avg_size
            self.db.update_whale_stats(shadow_id, volume, is_win, pnl, strategy_type)

    def get_whale_stats(self, shadow_id: str) -> Optional[Dict]:
        """Get statistics for a specific whale"""
        if self.db:
            db_stats = self.db.get_whale_stats(shadow_id)
            if db_stats:
                return db_stats

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
            "target_markets": len(self.target_markets),
            "tracked_whales": len(self.whale_profiles),
            "processed_trades": len(self._processed_trades),
            "db_connected": self.db is not None
        }

    async def close(self):
        """Close HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()

    # Legacy methods for compatibility
    def setup_websocket_handlers(self, client):
        """Legacy method - WebSocket handlers not used in polling mode"""
        self.logger.info("WebSocket handlers registered (polling mode active)")
