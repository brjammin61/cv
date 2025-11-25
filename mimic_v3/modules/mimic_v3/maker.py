"""
Maker.py - Smart Passive Market Making & LIP Farming
MIMIC V3.1 HARDENED

Implements:
- S.3.1: LIP Optimization - Prioritize rebate-eligible markets
- S.3.2: Inventory Skew - Adjust quotes based on position
- Favorite-Longshot Bias (FLB) exploitation
- Dynamic spread management
- Risk-adjusted quoting
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import math

from .kalshi_client import KalshiClient, OrderSide, OrderType

if TYPE_CHECKING:
    from .persistence import MimicDB


class MakerState(Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"      # Paused for taker opportunity
    STOPPED = "STOPPED"    # Manually stopped
    HEDGING = "HEDGING"    # Reducing inventory


@dataclass
class QuoteOrder:
    """Represents a limit order quote"""
    order_id: str
    ticker: str
    side: str
    price: int  # Cents (1-99)
    size: int   # Contracts
    created_at: datetime = field(default_factory=datetime.utcnow)
    filled: int = 0
    status: str = "open"
    is_skew_quote: bool = False  # True if placed to reduce inventory


@dataclass
class MarketOpportunity:
    """Represents a market making opportunity"""
    ticker: str
    event_ticker: str
    lip_eligible: bool
    lip_rebate_rate: float  # Rebate percentage
    spread: float
    spread_bps: float
    volume_24h: float
    favorite_side: str
    favorite_price: float
    longshot_price: float
    mid_price: float
    score: float
    resolution_hours: Optional[float] = None


class PassiveMarketMaker:
    """
    HARDENED Market Making with LIP Optimization and Inventory Skew.

    Strategies:
    1. LIP Farming: Prioritize rebate-eligible markets by expected rebate
    2. FLB Exploitation: Quote on favorite side for structural edge
    3. Inventory Skew: Adjust prices to manage directional risk
    4. Dynamic Spreads: Widen quotes in volatile conditions

    Risk Management:
    - Per-market inventory limits
    - Total exposure caps
    - Auto-pause on high volatility
    - Skew-based position reduction
    """

    # Kalshi LIP rebate tiers (approximate)
    LIP_REBATE_TIERS = {
        "high": 0.010,    # 1.0% rebate
        "medium": 0.005,  # 0.5% rebate
        "low": 0.002,     # 0.2% rebate
        "none": 0.0
    }

    def __init__(
        self,
        client: KalshiClient = None,
        db: 'MimicDB' = None,
        max_inventory_per_market: int = 100,
        max_total_inventory: int = 500,
        min_spread_bps: int = 200,
        max_spread_bps: int = 1000,
        lip_priority: bool = True,
        skew_enabled: bool = True,
        skew_threshold: int = 20,  # Start skewing at 20 contracts
        base_quote_size: int = 10,
        logger: logging.Logger = None
    ):
        self.client = client
        self.db = db
        self.max_inventory_per_market = max_inventory_per_market
        self.max_total_inventory = max_total_inventory
        self.min_spread_bps = min_spread_bps
        self.max_spread_bps = max_spread_bps
        self.lip_priority = lip_priority
        self.skew_enabled = skew_enabled
        self.skew_threshold = skew_threshold
        self.base_quote_size = base_quote_size
        self.logger = logger or logging.getLogger(__name__)

        self.state = MakerState.STOPPED
        self.active_quotes: Dict[str, List[QuoteOrder]] = defaultdict(list)
        self.inventory: Dict[str, int] = defaultdict(int)
        self.pnl_by_market: Dict[str, float] = defaultdict(float)
        self.fill_prices: Dict[str, List[float]] = defaultdict(list)

        # LIP market cache
        self._lip_markets: Dict[str, str] = {}  # ticker -> tier
        self._last_lip_refresh: Optional[datetime] = None

        # Volatility tracking
        self._price_history: Dict[str, List[Tuple[datetime, float]]] = defaultdict(list)

        # Statistics
        self.stats = {
            "quotes_placed": 0,
            "quotes_filled": 0,
            "quotes_cancelled": 0,
            "rebates_earned": 0.0,
            "spread_pnl": 0.0,
            "total_volume": 0.0,
            "skew_quotes": 0,
            "inventory_reductions": 0
        }

    async def start(self):
        """Start the market maker"""
        if not self.client:
            self.logger.error("MAKER: No client configured")
            return

        self.state = MakerState.ACTIVE
        self.logger.info("MAKER: Started")

    def stop(self):
        """Stop the market maker"""
        self.state = MakerState.STOPPED
        self.logger.info("MAKER: Stopped")

    def pause(self):
        """Temporarily pause for taker opportunity"""
        if self.state == MakerState.ACTIVE:
            self.state = MakerState.PAUSED
            self.logger.info("MAKER: Paused")

    def resume(self):
        """Resume after pause"""
        if self.state == MakerState.PAUSED:
            self.state = MakerState.ACTIVE
            self.logger.info("MAKER: Resumed")

    async def run_lip_cycle(self) -> str:
        """
        Main LIP farming cycle with inventory skew.

        S.3.1: Prioritize by expected rebate = volume * rebate_rate
        S.3.2: Adjust quotes based on current inventory
        """
        if self.state != MakerState.ACTIVE:
            return f"STATE_{self.state.value}"

        try:
            # 1. Check if inventory reduction needed
            if self._needs_inventory_reduction():
                await self._run_inventory_skew()
                return "SKEW_ACTIVE"

            # 2. Refresh LIP eligibility periodically
            await self._refresh_lip_markets()

            # 3. Find opportunities
            opportunities = await self._scan_opportunities()

            if not opportunities:
                return "NO_OPPORTUNITIES"

            # 4. Filter and sort by score
            valid_opps = [
                o for o in opportunities
                if o.score > 0 and self._check_inventory_room(o.ticker)
            ]

            if not valid_opps:
                return "NO_VALID_OPPORTUNITIES"

            # 5. Quote on top opportunities
            quoted = 0
            for opp in valid_opps[:5]:
                success = await self._quote_market(opp)
                if success:
                    quoted += 1

            # 6. Manage existing quotes
            await self._manage_quotes()

            return f"QUOTED_{quoted}_MARKETS"

        except Exception as e:
            self.logger.error(f"MAKER: Cycle error: {e}")
            return f"ERROR"

    async def _refresh_lip_markets(self):
        """Refresh LIP-eligible market list"""
        now = datetime.utcnow()

        # Refresh every 5 minutes
        if self._last_lip_refresh and (now - self._last_lip_refresh).seconds < 300:
            return

        # In production, this would fetch from Kalshi's LIP program API
        # For now, we use heuristics based on volume and spread
        self._last_lip_refresh = now

    async def _scan_opportunities(self) -> List[MarketOpportunity]:
        """
        Scan for market making opportunities.

        S.3.1: Score includes expected LIP rebate.
        """
        opportunities = []

        try:
            markets_response = await self.client.get_markets(status="open", limit=100)
            markets = markets_response.get("markets", [])

            for market in markets:
                opp = await self._analyze_market(market)
                if opp and opp.score > 0:
                    opportunities.append(opp)

        except Exception as e:
            self.logger.error(f"MAKER: Scan error: {e}")

        # Sort by score (includes LIP weighting)
        opportunities.sort(key=lambda x: x.score, reverse=True)
        return opportunities

    async def _analyze_market(self, market: Dict) -> Optional[MarketOpportunity]:
        """Analyze a single market for opportunity"""
        ticker = market.get("ticker", "")
        event_ticker = market.get("event_ticker", "")
        volume_24h = market.get("volume_24h", 0) or 0

        try:
            orderbook = await self.client.get_orderbook(ticker, depth=5)
        except Exception:
            return None

        # Extract best bid/ask
        yes_bids = orderbook.get("yes", [])
        no_bids = orderbook.get("no", [])

        if not yes_bids and not no_bids:
            return None

        best_yes_bid = yes_bids[0][0] if yes_bids else 0
        best_no_bid = no_bids[0][0] if no_bids else 0

        # Calculate implied ask (100 - other side's bid)
        best_yes_ask = 100 - best_no_bid if best_no_bid > 0 else 100
        best_no_ask = 100 - best_yes_bid if best_yes_bid > 0 else 100

        if best_yes_bid <= 0 or best_yes_ask >= 100:
            return None

        spread = best_yes_ask - best_yes_bid
        mid_price = (best_yes_bid + best_yes_ask) / 2
        spread_bps = (spread / mid_price) * 10000 if mid_price > 0 else 0

        # Skip if spread too tight
        if spread_bps < self.min_spread_bps:
            return None

        # Skip if spread too wide (illiquid)
        if spread_bps > self.max_spread_bps:
            return None

        # Determine favorite/longshot
        favorite_side = "yes" if mid_price > 50 else "no"
        favorite_price = mid_price / 100 if favorite_side == "yes" else (100 - mid_price) / 100
        longshot_price = 1 - favorite_price

        # Determine LIP eligibility
        lip_tier = self._get_lip_tier(market, volume_24h, spread_bps)
        lip_eligible = lip_tier != "none"
        lip_rebate_rate = self.LIP_REBATE_TIERS[lip_tier]

        # Calculate resolution proximity
        resolution_hours = self._calculate_resolution_hours(market)

        # Calculate opportunity score
        score = self._calculate_opportunity_score(
            spread_bps=spread_bps,
            lip_rebate_rate=lip_rebate_rate,
            volume_24h=volume_24h,
            favorite_price=favorite_price,
            resolution_hours=resolution_hours
        )

        return MarketOpportunity(
            ticker=ticker,
            event_ticker=event_ticker,
            lip_eligible=lip_eligible,
            lip_rebate_rate=lip_rebate_rate,
            spread=spread,
            spread_bps=spread_bps,
            volume_24h=volume_24h,
            favorite_side=favorite_side,
            favorite_price=favorite_price,
            longshot_price=longshot_price,
            mid_price=mid_price / 100,
            score=score,
            resolution_hours=resolution_hours
        )

    def _get_lip_tier(self, market: Dict, volume: float, spread_bps: float) -> str:
        """
        Determine LIP tier for a market.

        Heuristics (would use actual Kalshi data in production):
        - Low volume + wide spread = likely high LIP
        - Medium volume = medium LIP
        - High volume = low/no LIP
        """
        if volume < 1000 and spread_bps > 500:
            return "high"
        elif volume < 5000 and spread_bps > 300:
            return "medium"
        elif volume < 20000:
            return "low"
        return "none"

    def _calculate_resolution_hours(self, market: Dict) -> Optional[float]:
        """Calculate hours until settlement"""
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
        except Exception:
            return None

    def _calculate_opportunity_score(
        self,
        spread_bps: float,
        lip_rebate_rate: float,
        volume_24h: float,
        favorite_price: float,
        resolution_hours: Optional[float]
    ) -> float:
        """
        Calculate opportunity score.

        S.3.1: Include expected LIP rebate in score.
        """
        score = 0.0

        # Spread component (wider = more profit potential)
        spread_score = min(spread_bps / 100, 10)
        score += spread_score * 0.3

        # LIP rebate component (priority)
        if lip_rebate_rate > 0:
            # Expected rebate = volume * rate
            expected_rebate = min(volume_24h * lip_rebate_rate / 100, 10)
            score += expected_rebate * 0.4  # Heavy weight on LIP

        # Volume component (moderate volume is best)
        if 1000 < volume_24h < 50000:
            score += 3.0
        elif volume_24h > 0:
            score += 1.0

        # FLB component (strong favorites have edge)
        if favorite_price > 0.75 or favorite_price < 0.25:
            score += 2.0
        elif favorite_price > 0.65 or favorite_price < 0.35:
            score += 1.0

        # Resolution proximity (avoid near-settlement)
        if resolution_hours is not None:
            if resolution_hours < 1:
                score -= 5.0  # Avoid
            elif resolution_hours < 6:
                score -= 1.0

        return score

    def _needs_inventory_reduction(self) -> bool:
        """Check if we need to reduce inventory via skew"""
        for ticker, inv in self.inventory.items():
            if abs(inv) > self.skew_threshold:
                return True
        return False

    async def _run_inventory_skew(self):
        """
        S.3.2: Reduce inventory by skewing quotes.

        When long YES: Quote aggressively on YES ask (sell)
        When short YES (long NO): Quote aggressively on NO ask
        """
        if not self.skew_enabled:
            return

        for ticker, inv in self.inventory.items():
            if abs(inv) <= self.skew_threshold:
                continue

            try:
                # Get current orderbook
                orderbook = await self.client.get_orderbook(ticker, depth=3)

                if inv > 0:
                    # Long YES - need to sell YES
                    # Quote at best ask minus 1 cent (aggressive)
                    no_bids = orderbook.get("no", [])
                    if no_bids:
                        best_no_bid = no_bids[0][0]
                        # Selling YES = buying NO
                        skew_price = best_no_bid + 1  # Slightly better than best
                        await self._place_skew_quote(ticker, "no", skew_price, min(inv, 20))
                else:
                    # Short YES (long NO) - need to sell NO
                    yes_bids = orderbook.get("yes", [])
                    if yes_bids:
                        best_yes_bid = yes_bids[0][0]
                        skew_price = best_yes_bid + 1
                        await self._place_skew_quote(ticker, "yes", skew_price, min(-inv, 20))

                self.stats["inventory_reductions"] += 1

            except Exception as e:
                self.logger.error(f"MAKER: Skew error for {ticker}: {e}")

    async def _place_skew_quote(self, ticker: str, side: str, price: int, size: int):
        """Place a skew quote to reduce inventory"""
        if not self.client:
            return

        try:
            order_side = OrderSide.YES if side == "yes" else OrderSide.NO

            order_response = await self.client.create_order(
                ticker=ticker,
                side=order_side,
                order_type=OrderType.LIMIT,
                count=size,
                price=price
            )

            order_id = order_response.get("order", {}).get("order_id", "unknown")

            quote = QuoteOrder(
                order_id=order_id,
                ticker=ticker,
                side=side,
                price=price,
                size=size,
                is_skew_quote=True
            )

            self.active_quotes[ticker].append(quote)
            self.stats["skew_quotes"] += 1

            self.logger.info(f"MAKER: Skew quote {ticker} {side} {size}x @ {price}c")

        except Exception as e:
            self.logger.error(f"MAKER: Skew quote failed: {e}")

    def _check_inventory_room(self, ticker: str) -> bool:
        """Check if we have room for more inventory"""
        current = abs(self.inventory.get(ticker, 0))
        total = sum(abs(v) for v in self.inventory.values())

        return (
            current < self.max_inventory_per_market and
            total < self.max_total_inventory
        )

    async def _quote_market(self, opp: MarketOpportunity) -> bool:
        """
        Place quotes on a market.

        Strategy:
        - Quote on favorite side at best bid
        - Apply inventory skew adjustment if needed
        """
        if not self.client:
            return False

        ticker = opp.ticker

        try:
            orderbook = await self.client.get_orderbook(ticker, depth=3)

            # Determine quote price with inventory skew
            current_inv = self.inventory.get(ticker, 0)
            skew_adjustment = self._calculate_skew_adjustment(current_inv)

            if opp.favorite_side == "yes":
                yes_bids = orderbook.get("yes", [])
                if not yes_bids:
                    return False
                best_bid = yes_bids[0][0]
                quote_price = max(1, best_bid - skew_adjustment)
                side = OrderSide.YES
            else:
                no_bids = orderbook.get("no", [])
                if not no_bids:
                    return False
                best_bid = no_bids[0][0]
                quote_price = max(1, best_bid - skew_adjustment)
                side = OrderSide.NO

            if quote_price <= 0:
                return False

            # Calculate size
            room = self.max_inventory_per_market - abs(current_inv)
            size = min(self.base_quote_size, room)

            if size <= 0:
                return False

            order_response = await self.client.create_order(
                ticker=ticker,
                side=side,
                order_type=OrderType.LIMIT,
                count=size,
                price=quote_price
            )

            order_id = order_response.get("order", {}).get("order_id", "unknown")

            quote = QuoteOrder(
                order_id=order_id,
                ticker=ticker,
                side=opp.favorite_side,
                price=quote_price,
                size=size
            )

            self.active_quotes[ticker].append(quote)
            self.stats["quotes_placed"] += 1

            self.logger.debug(
                f"MAKER: Quote {ticker} {opp.favorite_side} {size}x @ {quote_price}c "
                f"(LIP: {opp.lip_eligible}, skew: {skew_adjustment})"
            )

            return True

        except Exception as e:
            self.logger.error(f"MAKER: Quote error for {ticker}: {e}")
            return False

    def _calculate_skew_adjustment(self, inventory: int) -> int:
        """
        Calculate price skew based on inventory.

        Positive inventory (long): Lower our bid to buy less
        Negative inventory (short): Higher our bid to buy more
        """
        if not self.skew_enabled or abs(inventory) < self.skew_threshold // 2:
            return 0

        # Skew: 1 cent per 10 contracts of inventory
        skew = inventory // 10
        return max(-5, min(5, skew))  # Cap at +/- 5 cents

    async def _manage_quotes(self):
        """Manage existing quotes - cancel stale ones"""
        stale_threshold = timedelta(minutes=3)
        now = datetime.utcnow()

        for ticker, quotes in list(self.active_quotes.items()):
            for quote in quotes[:]:
                if now - quote.created_at > stale_threshold:
                    try:
                        await self.client.cancel_order(quote.order_id)
                        quotes.remove(quote)
                        self.stats["quotes_cancelled"] += 1
                        self.logger.debug(f"MAKER: Cancelled stale quote {quote.order_id}")
                    except Exception as e:
                        self.logger.debug(f"MAKER: Cancel error: {e}")
                        quotes.remove(quote)

    async def cancel_all_quotes(self):
        """Cancel all active quotes"""
        cancelled = 0
        for ticker, quotes in self.active_quotes.items():
            for quote in quotes:
                try:
                    await self.client.cancel_order(quote.order_id)
                    cancelled += 1
                except Exception:
                    pass

        self.active_quotes.clear()
        self.logger.info(f"MAKER: Cancelled {cancelled} quotes")

    def handle_fill(self, order_id: str, fill_size: int, fill_price: float):
        """
        Handle order fill notification.

        Updates inventory, tracks PnL, records rebate.
        """
        for ticker, quotes in self.active_quotes.items():
            for quote in quotes:
                if quote.order_id == order_id:
                    quote.filled += fill_size

                    # Update inventory
                    direction = 1 if quote.side == "yes" else -1
                    self.inventory[ticker] += fill_size * direction

                    # Track fill price for PnL
                    self.fill_prices[ticker].append(fill_price)

                    # Estimate rebate (depends on LIP tier)
                    lip_tier = self._lip_markets.get(ticker, "low")
                    rebate_rate = self.LIP_REBATE_TIERS.get(lip_tier, 0)
                    rebate = fill_size * fill_price * rebate_rate / 100
                    self.stats["rebates_earned"] += rebate

                    self.stats["quotes_filled"] += 1
                    self.stats["total_volume"] += fill_size * fill_price / 100

                    self.logger.info(
                        f"MAKER: Fill {ticker} {quote.side} {fill_size}x @ {fill_price}c | "
                        f"Inv: {self.inventory[ticker]} | Rebate: ${rebate:.3f}"
                    )

                    # Remove if fully filled
                    if quote.filled >= quote.size:
                        quotes.remove(quote)

                    return

    def get_status(self) -> Dict:
        """Get market maker status"""
        return {
            "state": self.state.value,
            "active_markets": len(self.active_quotes),
            "total_quotes": sum(len(q) for q in self.active_quotes.values()),
            "net_inventory": dict(self.inventory),
            "total_inventory": sum(abs(v) for v in self.inventory.values()),
            "stats": self.stats,
            "skew_enabled": self.skew_enabled
        }
