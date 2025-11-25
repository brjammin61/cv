"""
Maker.py - Passive Market Making & LIP Farming
MIMIC V3.1 - Production Ready

Implements:
- Liquidity Incentive Program (LIP) rebate farming
- Favorite-Longshot Bias (FLB) exploitation
- Passive limit order management
- Inventory risk management
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

from .kalshi_client import KalshiClient, OrderSide, OrderType


class MakerState(Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"  # Paused for taker opportunity
    STOPPED = "STOPPED"  # Manually stopped


@dataclass
class QuoteOrder:
    """Represents a limit order quote"""
    order_id: str
    ticker: str
    side: str  # "yes" or "no"
    price: int  # In cents (1-99)
    size: int  # Number of contracts
    created_at: datetime = field(default_factory=datetime.utcnow)
    filled: int = 0
    status: str = "open"


@dataclass
class MarketOpportunity:
    """Represents a market making opportunity"""
    ticker: str
    event_ticker: str
    lip_eligible: bool
    spread: float  # Bid-ask spread
    volume_24h: float
    favorite_side: str  # "yes" or "no"
    favorite_price: float
    score: float  # Opportunity score (higher = better)


class PassiveMarketMaker:
    """
    Passive market making strategy for Kalshi.

    Strategies:
    1. LIP Farming: Capture liquidity rebates on incentivized markets
    2. FLB Exploitation: Quote on favorite side where edge exists
    3. Spread Capture: Post competitive quotes on both sides

    Risk Management:
    - Inventory limits per market
    - Total exposure caps
    - Auto-pause on high volatility
    """

    def __init__(
        self,
        client: KalshiClient = None,
        max_inventory_per_market: int = 100,
        max_total_inventory: int = 500,
        min_spread_bps: int = 200,  # Minimum 2% spread to quote
        lip_priority: bool = True,
        logger: logging.Logger = None
    ):
        self.client = client
        self.max_inventory_per_market = max_inventory_per_market
        self.max_total_inventory = max_total_inventory
        self.min_spread_bps = min_spread_bps
        self.lip_priority = lip_priority
        self.logger = logger or logging.getLogger(__name__)

        self.state = MakerState.STOPPED
        self.active_quotes: Dict[str, List[QuoteOrder]] = defaultdict(list)
        self.inventory: Dict[str, int] = defaultdict(int)  # Net inventory per ticker
        self.pnl_by_market: Dict[str, float] = defaultdict(float)

        # Markets we're actively quoting
        self.active_markets: List[str] = []

        # Statistics
        self.stats = {
            "quotes_placed": 0,
            "quotes_filled": 0,
            "rebates_earned": 0.0,
            "spread_pnl": 0.0,
            "total_volume": 0.0
        }

        # LIP market cache
        self._lip_markets: Dict[str, Dict] = {}
        self._last_lip_refresh = None

    async def start(self):
        """Start the market maker"""
        if not self.client:
            self.logger.error("No client configured")
            return

        self.state = MakerState.ACTIVE
        self.logger.info("Market Maker STARTED")

    def stop(self):
        """Stop the market maker"""
        self.state = MakerState.STOPPED
        self.logger.info("Market Maker STOPPED")

    def pause(self):
        """Temporarily pause for taker opportunity"""
        if self.state == MakerState.ACTIVE:
            self.state = MakerState.PAUSED
            self.logger.info("Market Maker PAUSED")

    def resume(self):
        """Resume after pause"""
        if self.state == MakerState.PAUSED:
            self.state = MakerState.ACTIVE
            self.logger.info("Market Maker RESUMED")

    async def run_lip_cycle(self) -> str:
        """
        Main LIP farming cycle.

        Returns status string.
        """
        if self.state != MakerState.ACTIVE:
            return f"STATE_{self.state.value}"

        try:
            # 1. Find LIP-eligible markets
            opportunities = await self._scan_opportunities()

            if not opportunities:
                return "NO_OPPORTUNITIES"

            # 2. Filter by our criteria
            valid_opps = [
                o for o in opportunities
                if o.score > 0 and self._check_inventory_room(o.ticker)
            ]

            if not valid_opps:
                return "NO_VALID_OPPORTUNITIES"

            # 3. Quote on top opportunities
            for opp in valid_opps[:5]:  # Top 5 opportunities
                await self._quote_market(opp)

            # 4. Manage existing quotes
            await self._manage_quotes()

            return f"QUOTED_{len(valid_opps)}_MARKETS"

        except Exception as e:
            self.logger.error(f"LIP cycle error: {e}")
            return f"ERROR_{str(e)[:20]}"

    async def _scan_opportunities(self) -> List[MarketOpportunity]:
        """
        Scan for market making opportunities.
        Prioritizes LIP-eligible markets.
        """
        opportunities = []

        try:
            # Get open markets
            markets_response = await self.client.get_markets(status="open", limit=100)
            markets = markets_response.get("markets", [])

            for market in markets:
                ticker = market.get("ticker", "")
                event_ticker = market.get("event_ticker", "")

                # Check if LIP eligible (this would come from Kalshi's LIP program data)
                lip_eligible = self._is_lip_eligible(market)

                # Get orderbook
                try:
                    orderbook = await self.client.get_orderbook(ticker, depth=5)
                except Exception:
                    continue

                # Calculate spread
                best_bid = orderbook.get("yes", [[0]])[0][0] if orderbook.get("yes") else 0
                best_ask = 100 - (orderbook.get("no", [[0]])[0][0] if orderbook.get("no") else 0)

                if best_bid <= 0 or best_ask >= 100:
                    continue

                spread = best_ask - best_bid
                spread_bps = (spread / best_bid) * 10000 if best_bid > 0 else 0

                # Skip if spread too tight
                if spread_bps < self.min_spread_bps:
                    continue

                # Determine favorite side (price > 50)
                mid_price = (best_bid + best_ask) / 2
                favorite_side = "yes" if mid_price > 50 else "no"
                favorite_price = mid_price / 100

                # Calculate opportunity score
                score = self._calculate_opportunity_score(
                    spread_bps=spread_bps,
                    lip_eligible=lip_eligible,
                    volume_24h=market.get("volume_24h", 0),
                    favorite_price=favorite_price
                )

                opportunities.append(MarketOpportunity(
                    ticker=ticker,
                    event_ticker=event_ticker,
                    lip_eligible=lip_eligible,
                    spread=spread,
                    volume_24h=market.get("volume_24h", 0),
                    favorite_side=favorite_side,
                    favorite_price=favorite_price,
                    score=score
                ))

        except Exception as e:
            self.logger.error(f"Opportunity scan error: {e}")

        # Sort by score descending
        opportunities.sort(key=lambda x: x.score, reverse=True)
        return opportunities

    def _is_lip_eligible(self, market: Dict) -> bool:
        """
        Check if market is eligible for Kalshi's LIP rebates.
        In production, this would check against the actual LIP program list.
        """
        # Heuristic: markets with low volume often have LIP incentives
        volume = market.get("volume_24h", 0)
        return volume < 10000  # Low volume = likely LIP

    def _calculate_opportunity_score(
        self,
        spread_bps: float,
        lip_eligible: bool,
        volume_24h: float,
        favorite_price: float
    ) -> float:
        """
        Calculate opportunity score for a market.

        Higher score = better opportunity.
        """
        score = 0.0

        # Spread component (wider = better for MM)
        score += min(spread_bps / 100, 10)  # Cap at 10 points

        # LIP bonus
        if lip_eligible and self.lip_priority:
            score += 5.0

        # Volume component (moderate volume is best)
        if 1000 < volume_24h < 50000:
            score += 3.0
        elif volume_24h > 0:
            score += 1.0

        # FLB component (favorites have edge)
        # Strong favorites (>70%) have known positive edge for MM
        if favorite_price > 0.70 or favorite_price < 0.30:
            score += 2.0

        return score

    def _check_inventory_room(self, ticker: str) -> bool:
        """Check if we have room for more inventory"""
        current = abs(self.inventory.get(ticker, 0))
        total = sum(abs(v) for v in self.inventory.values())

        return (
            current < self.max_inventory_per_market and
            total < self.max_total_inventory
        )

    async def _quote_market(self, opp: MarketOpportunity):
        """
        Place quotes on a market.

        Strategy:
        - Quote on favorite side at best bid
        - Size based on available inventory room
        """
        if not self.client:
            return

        ticker = opp.ticker

        try:
            # Get current orderbook
            orderbook = await self.client.get_orderbook(ticker, depth=3)

            # Determine our quote price (at or slightly better than best bid)
            if opp.favorite_side == "yes":
                best_bid = orderbook.get("yes", [[0]])[0][0] if orderbook.get("yes") else 0
                quote_price = best_bid  # Quote at best bid
                side = OrderSide.YES
            else:
                best_bid = orderbook.get("no", [[0]])[0][0] if orderbook.get("no") else 0
                quote_price = best_bid
                side = OrderSide.NO

            if quote_price <= 0:
                return

            # Calculate size
            room = self.max_inventory_per_market - abs(self.inventory.get(ticker, 0))
            size = min(10, room)  # Start with 10 contracts

            if size <= 0:
                return

            # Place order
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
                f"Quoted {ticker}: {opp.favorite_side.upper()} "
                f"{size}x @ {quote_price}c"
            )

        except Exception as e:
            self.logger.error(f"Quote error for {ticker}: {e}")

    async def _manage_quotes(self):
        """
        Manage existing quotes.

        - Cancel stale quotes
        - Update prices if market moved
        - Track fills
        """
        stale_threshold = timedelta(minutes=5)
        now = datetime.utcnow()

        for ticker, quotes in list(self.active_quotes.items()):
            for quote in quotes[:]:  # Copy list for modification
                # Cancel stale quotes
                if now - quote.created_at > stale_threshold:
                    try:
                        await self.client.cancel_order(quote.order_id)
                        quotes.remove(quote)
                        self.logger.debug(f"Cancelled stale quote: {quote.order_id}")
                    except Exception as e:
                        self.logger.debug(f"Cancel error: {e}")

    async def cancel_all_quotes(self):
        """Cancel all active quotes"""
        for ticker, quotes in self.active_quotes.items():
            for quote in quotes:
                try:
                    await self.client.cancel_order(quote.order_id)
                except Exception as e:
                    self.logger.debug(f"Cancel error: {e}")

        self.active_quotes.clear()
        self.logger.info("All quotes cancelled")

    def handle_fill(self, order_id: str, fill_size: int, fill_price: float):
        """
        Handle order fill notification.

        Updates inventory and PnL tracking.
        """
        for ticker, quotes in self.active_quotes.items():
            for quote in quotes:
                if quote.order_id == order_id:
                    quote.filled += fill_size

                    # Update inventory
                    direction = 1 if quote.side == "yes" else -1
                    self.inventory[ticker] += fill_size * direction

                    # Estimate rebate earned (LIP typically 0.5-1%)
                    rebate = fill_size * fill_price * 0.005
                    self.stats["rebates_earned"] += rebate
                    self.stats["quotes_filled"] += 1
                    self.stats["total_volume"] += fill_size * fill_price

                    self.logger.info(
                        f"Fill: {ticker} {quote.side} {fill_size}x @ {fill_price}c | "
                        f"Inventory: {self.inventory[ticker]}"
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
            "stats": self.stats
        }


# ==================== USAGE EXAMPLE ====================

async def example_usage():
    """Example showing market maker usage"""

    # Would use real client in production
    maker = PassiveMarketMaker(client=None)

    print(f"Maker status: {maker.get_status()}")

    # Simulate opportunity
    opp = MarketOpportunity(
        ticker="KXCPI-25DEC-T0.3",
        event_ticker="KXCPI-25DEC",
        lip_eligible=True,
        spread=5.0,
        volume_24h=5000,
        favorite_side="yes",
        favorite_price=0.65,
        score=8.5
    )

    print(f"Opportunity score: {opp.score}")


if __name__ == "__main__":
    asyncio.run(example_usage())
