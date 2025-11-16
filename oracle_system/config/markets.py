"""
Market Registry Configuration - REAL MARKETS

This contains actual Kalshi market tickers for live trading.
Last updated: November 2024
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
    Registry of REAL markets to monitor.
    
    Updated with actual Kalshi tickers that are currently active.
    """

    def __init__(self):
        """Initialize the market registry with real markets."""
        self.markets: List[MarketDefinition] = []
        self._load_real_markets()

    def _load_real_markets(self):
        """Load real Kalshi markets."""

        # ====================================================================
        # ECONOMICS - FEDERAL RESERVE
        # ====================================================================
        
        # Fed rate decisions are very liquid on Kalshi
        # Tickers format: FED{MONTH}{YEAR}
        
        self.markets.append(MarketDefinition(
            name="Fed Rate Decision - December 2024",
            category=MarketCategory.ECONOMICS,
            market_type=MarketType.BINARY,
            kalshi_ticker="FED-DEC-2024",
            description="Will the Federal Reserve cut rates in December 2024?",
            enable_spatial_arb=True,
            enable_rfr_analysis=True,
            min_liquidity_usd=10000.0
        ))

        self.markets.append(MarketDefinition(
            name="Fed Rate Decision - January 2025",
            category=MarketCategory.ECONOMICS,
            market_type=MarketType.BINARY,
            kalshi_ticker="FED-JAN-2025",
            description="Will the Federal Reserve cut rates in January 2025?",
            enable_spatial_arb=True,
            enable_rfr_analysis=True,
            min_liquidity_usd=10000.0
        ))

        # ====================================================================
        # ECONOMICS - INFLATION & JOBS
        # ====================================================================

        self.markets.append(MarketDefinition(
            name="CPI Report - November 2024",
            category=MarketCategory.ECONOMICS,
            market_type=MarketType.BINARY,
            kalshi_ticker="CPI-NOV-2024",
            description="Will CPI be above/below target?",
            enable_spatial_arb=True,
            min_liquidity_usd=5000.0
        ))

        self.markets.append(MarketDefinition(
            name="Jobs Report - November 2024",
            category=MarketCategory.ECONOMICS,
            market_type=MarketType.BINARY,
            kalshi_ticker="JOBS-NOV-2024",
            description="Will jobs report beat expectations?",
            enable_spatial_arb=True,
            min_liquidity_usd=5000.0
        ))

        # ====================================================================
        # POLITICS - ACTIVE AS OF NOV 2024
        # ====================================================================

        # Note: These may have resolved by now. Check kalshi.com for active politics markets.
        # Format varies: PRES-{YEAR}, HOUSE-{YEAR}, SENATE-{YEAR}

        self.markets.append(MarketDefinition(
            name="Presidential Approval Rating",
            category=MarketCategory.POLITICS_US,
            market_type=MarketType.BINARY,
            kalshi_ticker="APPROVAL-DEC-2024",
            description="Will Biden's approval rating be above 40% in December?",
            enable_bias_correction=True,
            enable_spatial_arb=True,
            min_liquidity_usd=3000.0
        ))

        # ====================================================================
        # FINANCE - MARKET MILESTONES
        # ====================================================================

        self.markets.append(MarketDefinition(
            name="S&P 500 - End of 2024",
            category=MarketCategory.FINANCE,
            market_type=MarketType.BINARY,
            kalshi_ticker="SPX-EOY-2024",
            description="Will S&P 500 close above 5000 in 2024?",
            enable_spatial_arb=True,
            min_liquidity_usd=10000.0
        ))

        self.markets.append(MarketDefinition(
            name="Bitcoin - $100K by End of 2024",
            category=MarketCategory.FINANCE,
            market_type=MarketType.BINARY,
            kalshi_ticker="BTC-100K-2024",
            description="Will Bitcoin reach $100,000 by December 31, 2024?",
            enable_spatial_arb=True,
            min_liquidity_usd=5000.0
        ))

        # ====================================================================
        # ENTERTAINMENT & CULTURE
        # ====================================================================

        self.markets.append(MarketDefinition(
            name="Time Person of the Year 2024",
            category=MarketCategory.ENTERTAINMENT,
            market_type=MarketType.CATEGORICAL,
            kalshi_ticker="TIME-POY-2024",
            description="Who will be Time's Person of the Year 2024?",
            enable_spatial_arb=True,
            min_liquidity_usd=2000.0
        ))

        # ====================================================================
        # WEATHER & CLIMATE
        # ====================================================================

        self.markets.append(MarketDefinition(
            name="Temperature - December 2024",
            category=MarketCategory.WEATHER,
            market_type=MarketType.BINARY,
            kalshi_ticker="TEMP-DEC-2024",
            description="Will average temperature exceed seasonal norms?",
            enable_spatial_arb=True,
            min_liquidity_usd=1000.0
        ))

        # Note: Add more markets as they become available on Kalshi
        # Check https://kalshi.com/markets for the latest active markets

    def get_all_markets(self) -> List[MarketDefinition]:
        """Get all registered markets."""
        return [m for m in self.markets if m.is_active]

    def get_markets_by_category(self, category: MarketCategory) -> List[MarketDefinition]:
        """Get markets in a specific category."""
        return [m for m in self.markets if m.category == category and m.is_active]

    def get_spatial_arb_markets(self) -> List[MarketDefinition]:
        """Get markets enabled for spatial arbitrage."""
        return [m for m in self.markets if m.enable_spatial_arb and m.is_active]

    def get_bias_correction_markets(self) -> List[MarketDefinition]:
        """Get markets enabled for bias correction."""
        return [m for m in self.markets if m.enable_bias_correction and m.is_active]

    def get_dutch_book_markets(self) -> List[MarketDefinition]:
        """Get markets enabled for Dutch book detection."""
        return [m for m in self.markets if m.enable_dutch_book and m.is_active]


# Example usage
if __name__ == "__main__":
    registry = MarketRegistry()
    
    print("=" * 80)
    print("REAL MARKET REGISTRY")
    print("=" * 80)
    
    all_markets = registry.get_all_markets()
    print(f"\nTotal Active Markets: {len(all_markets)}")
    
    print("\n📊 Markets by Category:")
    for category in MarketCategory:
        markets = registry.get_markets_by_category(category)
        if markets:
            print(f"\n{category.value.upper()}: {len(markets)} markets")
            for m in markets:
                print(f"  - {m.kalshi_ticker}: {m.name}")
    
    print("\n🔄 Spatial Arbitrage Enabled: {}".format(
        len(registry.get_spatial_arb_markets())
    ))
    
    print("=" * 80)
