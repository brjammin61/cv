"""
Market Registry Configuration

This module defines the markets to monitor across Kalshi and Polymarket.
Update this file to add new markets or modify existing ones.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import date
from enum import Enum


class MarketCategory(Enum):
    """Categories of prediction markets."""
    POLITICS_US = "politics_us"
    POLITICS_INTL = "politics_intl"
    ECONOMICS = "economics"
    FINANCE = "finance"
    SPORTS = "sports"
    ENTERTAINMENT = "entertainment"
    SCIENCE = "science"
    WEATHER = "weather"
    OTHER = "other"


class MarketType(Enum):
    """Types of market structures."""
    BINARY = "binary"  # Simple yes/no
    CATEGORICAL = "categorical"  # Multiple mutually exclusive outcomes
    SCALAR = "scalar"  # Numeric range


@dataclass
class MarketDefinition:
    """Definition of a single prediction market."""

    # Human-readable market name
    name: str

    # Market category
    category: MarketCategory

    # Market type
    market_type: MarketType

    # Resolution date
    resolution_date: Optional[date] = None

    # Kalshi market identifier
    kalshi_ticker: Optional[str] = None
    kalshi_market_id: Optional[str] = None

    # Polymarket market identifier
    polymarket_condition_id: Optional[str] = None
    polymarket_market_slug: Optional[str] = None
    polymarket_yes_token_id: Optional[str] = None
    polymarket_no_token_id: Optional[str] = None

    # For categorical markets (Dutch Book detection)
    outcomes: Optional[Dict[str, str]] = None

    # Market metadata
    description: Optional[str] = None
    is_active: bool = True
    min_liquidity_usd: float = 1000.0

    # Which strategies apply to this market
    enable_bias_correction: bool = False
    enable_spatial_arb: bool = True
    enable_dutch_book: bool = False
    enable_rfr_analysis: bool = False


class MarketRegistry:
    """
    Registry of all markets to monitor.

    This class manages the list of markets and provides methods to
    query and filter markets by various criteria.
    """

    def __init__(self):
        """Initialize the market registry with default markets."""
        self.markets: List[MarketDefinition] = []
        self._load_default_markets()

    def _load_default_markets(self):
        """Load the default set of markets to monitor."""

        # EXAMPLE MARKETS - Replace these with actual market IDs from the exchanges

        # ====================================================================
        # POLITICS - US ELECTIONS
        # ====================================================================

        self.markets.append(MarketDefinition(
            name="Presidential Election 2028 - Republican Nominee",
            category=MarketCategory.POLITICS_US,
            market_type=MarketType.CATEGORICAL,
            resolution_date=date(2028, 7, 20),
            # kalshi_ticker="PREZ-28-REP",
            # polymarket_condition_id="0x...",
            outcomes={
                "Trump": "outcome_token_1",
                "DeSantis": "outcome_token_2",
                "Haley": "outcome_token_3",
                "Other": "outcome_token_4"
            },
            description="Who will win the 2028 Republican nomination?",
            enable_bias_correction=True,
            enable_spatial_arb=False,
            enable_dutch_book=True,
            enable_rfr_analysis=True
        ))

        self.markets.append(MarketDefinition(
            name="2028 Presidential Election Winner",
            category=MarketCategory.POLITICS_US,
            market_type=MarketType.BINARY,
            resolution_date=date(2028, 11, 8),
            # kalshi_ticker="PREZ-28",
            # polymarket_condition_id="0x...",
            # polymarket_yes_token_id="123456",
            description="Will the Republican candidate win the 2028 election?",
            enable_bias_correction=True,
            enable_spatial_arb=True,
            enable_dutch_book=False,
            enable_rfr_analysis=True
        ))

        # ====================================================================
        # ECONOMICS
        # ====================================================================

        self.markets.append(MarketDefinition(
            name="Fed Rate Cut - December 2026",
            category=MarketCategory.ECONOMICS,
            market_type=MarketType.BINARY,
            resolution_date=date(2026, 12, 18),
            # kalshi_ticker="FED-CUT-DEC26",
            # polymarket_condition_id="0x...",
            description="Will the Fed cut rates in December 2026?",
            enable_spatial_arb=True,
            enable_rfr_analysis=True
        ))

        self.markets.append(MarketDefinition(
            name="CPI Above 3% - Q1 2026",
            category=MarketCategory.ECONOMICS,
            market_type=MarketType.BINARY,
            resolution_date=date(2026, 4, 15),
            # kalshi_ticker="CPI-3-Q126",
            # polymarket_condition_id="0x...",
            description="Will Q1 2026 CPI be above 3%?",
            enable_spatial_arb=True,
            enable_rfr_analysis=False
        ))

        # ====================================================================
        # FINANCE
        # ====================================================================

        self.markets.append(MarketDefinition(
            name="Bitcoin Above $100k - 2026",
            category=MarketCategory.FINANCE,
            market_type=MarketType.BINARY,
            resolution_date=date(2026, 12, 31),
            # kalshi_ticker="BTC-100K-26",
            # polymarket_condition_id="0x...",
            description="Will Bitcoin trade above $100k in 2026?",
            enable_spatial_arb=True,
            enable_rfr_analysis=True
        ))

        # ====================================================================
        # TEMPLATE FOR ADDING NEW MARKETS
        # ====================================================================
        # Uncomment and fill in the template below to add new markets:
        #
        # self.markets.append(MarketDefinition(
        #     name="Your Market Name",
        #     category=MarketCategory.OTHER,
        #     market_type=MarketType.BINARY,
        #     resolution_date=date(2026, 12, 31),
        #     kalshi_ticker="YOUR-KALSHI-TICKER",
        #     polymarket_condition_id="0xYOUR_POLY_CONDITION_ID",
        #     polymarket_yes_token_id="your_yes_token_id",
        #     description="Your market description",
        #     enable_bias_correction=False,
        #     enable_spatial_arb=True,
        #     enable_dutch_book=False,
        #     enable_rfr_analysis=False
        # ))

    def get_all_markets(self) -> List[MarketDefinition]:
        """Get all registered markets."""
        return [m for m in self.markets if m.is_active]

    def get_markets_by_category(self, category: MarketCategory) -> List[MarketDefinition]:
        """Get all markets in a specific category."""
        return [m for m in self.markets if m.category == category and m.is_active]

    def get_markets_by_type(self, market_type: MarketType) -> List[MarketDefinition]:
        """Get all markets of a specific type."""
        return [m for m in self.markets if m.market_type == market_type and m.is_active]

    def get_spatial_arb_markets(self) -> List[MarketDefinition]:
        """Get all markets eligible for spatial arbitrage."""
        return [
            m for m in self.markets
            if m.enable_spatial_arb
            and m.kalshi_ticker is not None
            and m.polymarket_condition_id is not None
            and m.is_active
        ]

    def get_dutch_book_markets(self) -> List[MarketDefinition]:
        """Get all markets eligible for Dutch Book arbitrage."""
        return [
            m for m in self.markets
            if m.enable_dutch_book
            and m.market_type == MarketType.CATEGORICAL
            and m.outcomes is not None
            and m.is_active
        ]

    def get_bias_correction_markets(self) -> List[MarketDefinition]:
        """Get all markets eligible for bias correction analysis."""
        return [
            m for m in self.markets
            if m.enable_bias_correction
            and m.is_active
        ]

    def get_rfr_markets(self) -> List[MarketDefinition]:
        """Get all markets eligible for risk-free rate analysis."""
        return [
            m for m in self.markets
            if m.enable_rfr_analysis
            and m.resolution_date is not None
            and m.is_active
        ]

    def get_market_by_name(self, name: str) -> Optional[MarketDefinition]:
        """Get a market by its exact name."""
        for market in self.markets:
            if market.name == name:
                return market
        return None

    def get_market_by_kalshi_ticker(self, ticker: str) -> Optional[MarketDefinition]:
        """Get a market by its Kalshi ticker."""
        for market in self.markets:
            if market.kalshi_ticker == ticker:
                return market
        return None

    def get_market_by_polymarket_id(self, condition_id: str) -> Optional[MarketDefinition]:
        """Get a market by its Polymarket condition ID."""
        for market in self.markets:
            if market.polymarket_condition_id == condition_id:
                return market
        return None

    def add_market(self, market: MarketDefinition) -> None:
        """Add a new market to the registry."""
        # Check for duplicates
        existing = self.get_market_by_name(market.name)
        if existing:
            raise ValueError(f"Market '{market.name}' already exists in registry")

        self.markets.append(market)

    def deactivate_market(self, name: str) -> None:
        """Deactivate a market (don't delete, just mark inactive)."""
        market = self.get_market_by_name(name)
        if market:
            market.is_active = False

    def print_summary(self) -> None:
        """Print a summary of all registered markets."""
        print("=" * 80)
        print("MARKET REGISTRY SUMMARY")
        print("=" * 80)

        active_markets = self.get_all_markets()
        print(f"\nTotal Active Markets: {len(active_markets)}")

        print("\nBy Category:")
        for category in MarketCategory:
            count = len(self.get_markets_by_category(category))
            if count > 0:
                print(f"  {category.value}: {count}")

        print("\nBy Strategy:")
        print(f"  Spatial Arbitrage: {len(self.get_spatial_arb_markets())}")
        print(f"  Dutch Book: {len(self.get_dutch_book_markets())}")
        print(f"  Bias Correction: {len(self.get_bias_correction_markets())}")
        print(f"  RFR Analysis: {len(self.get_rfr_markets())}")

        print("\nMarket Details:")
        print("-" * 80)
        for market in active_markets:
            print(f"\n{market.name}")
            print(f"  Category: {market.category.value}")
            print(f"  Type: {market.market_type.value}")
            if market.resolution_date:
                print(f"  Resolution: {market.resolution_date}")
            if market.kalshi_ticker:
                print(f"  Kalshi: {market.kalshi_ticker}")
            if market.polymarket_condition_id:
                print(f"  Polymarket: {market.polymarket_condition_id[:16]}...")
            strategies = []
            if market.enable_spatial_arb:
                strategies.append("SpatialArb")
            if market.enable_dutch_book:
                strategies.append("DutchBook")
            if market.enable_bias_correction:
                strategies.append("BiasCorrection")
            if market.enable_rfr_analysis:
                strategies.append("RFR")
            print(f"  Strategies: {', '.join(strategies)}")


# Create a global default registry
default_registry = MarketRegistry()


# Example usage and testing
if __name__ == "__main__":
    print("Market Registry Module - Example Usage\n")

    # Create registry
    registry = MarketRegistry()

    # Print summary
    registry.print_summary()

    # Query specific markets
    print("\n" + "=" * 80)
    print("Querying Markets")
    print("=" * 80)

    print("\nSpatial Arbitrage Opportunities:")
    for market in registry.get_spatial_arb_markets():
        print(f"  - {market.name}")

    print("\nDutch Book Opportunities:")
    for market in registry.get_dutch_book_markets():
        print(f"  - {market.name} ({len(market.outcomes or {})} outcomes)")

    print("\nBias Correction Candidates:")
    for market in registry.get_bias_correction_markets():
        print(f"  - {market.name}")
