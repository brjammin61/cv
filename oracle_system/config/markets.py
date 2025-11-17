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
        """Load real Kalshi markets - VERIFIED NOV 17, 2025."""

        # ====================================================================
        # CRYPTO - HIGHEST VOLUME MARKETS
        # ====================================================================

        self.markets.append(MarketDefinition(
            name="Bitcoin Reserve 2026",
            category=MarketCategory.FINANCE,
            market_type=MarketType.BINARY,
            kalshi_ticker="KXBTCRESERVE-26-JAN01",
            description="Bitcoin Reserve by Jan 2026 (Volume: 2,298,247)",
            enable_spatial_arb=True,
            min_liquidity_usd=100000.0
        ))

        self.markets.append(MarketDefinition(
            name="Bitcoin $150K by May 2026",
            category=MarketCategory.FINANCE,
            market_type=MarketType.BINARY,
            kalshi_ticker="KXBTCMAX150-25-26MAY31-149999.99",
            description="BTC hits $150K by May 2026 (Volume: 440,594)",
            enable_spatial_arb=True,
            min_liquidity_usd=50000.0
        ))

        self.markets.append(MarketDefinition(
            name="Bitcoin $150K by Apr 2026",
            category=MarketCategory.FINANCE,
            market_type=MarketType.BINARY,
            kalshi_ticker="KXBTCMAX150-25-26APR30-149999.99",
            description="BTC hits $150K by April 2026 (Volume: 164,861)",
            enable_spatial_arb=True,
            min_liquidity_usd=20000.0
        ))

        # ====================================================================
        # FINANCIALS - HIGH VOLUME
        # ====================================================================

        self.markets.append(MarketDefinition(
            name="S&P 500 Max 2026 - $6999",
            category=MarketCategory.FINANCE,
            market_type=MarketType.BINARY,
            kalshi_ticker="KXINXMAXY-26-6999.99",
            description="S&P 500 max $6999.99 in 2026 (Volume: 171,285)",
            enable_spatial_arb=True,
            min_liquidity_usd=20000.0
        ))

        self.markets.append(MarketDefinition(
            name="S&P 500 Max 2026 - $7499",
            category=MarketCategory.FINANCE,
            market_type=MarketType.BINARY,
            kalshi_ticker="KXINXMAXY-26-7499.99",
            description="S&P 500 max $7499.99 in 2026 (Volume: 31,881)",
            enable_spatial_arb=True,
            min_liquidity_usd=10000.0
        ))

        # ====================================================================
        # POLITICS - ACTIVE TRADING
        # ====================================================================

        self.markets.append(MarketDefinition(
            name="DC Federalization by Jan 2027",
            category=MarketCategory.POLITICS_US,
            market_type=MarketType.BINARY,
            kalshi_ticker="KXFEDDC-27JAN-FEDDC",
            description="DC Federalization by Jan 2027 (Volume: 32,835)",
            enable_bias_correction=True,
            enable_spatial_arb=True,
            min_liquidity_usd=10000.0
        ))

        self.markets.append(MarketDefinition(
            name="House VA-7 Democrat",
            category=MarketCategory.POLITICS_US,
            market_type=MarketType.BINARY,
            kalshi_ticker="HOUSEVA7-26-D",
            description="House Virginia 7th District Dem (Volume: 1,238)",
            enable_bias_correction=True,
            enable_spatial_arb=True,
            min_liquidity_usd=1000.0
        ))

        # ====================================================================
        # ECONOMICS - REAL MARKETS
        # ====================================================================

        self.markets.append(MarketDefinition(
            name="Texas Gas Price >= $3",
            category=MarketCategory.ECONOMICS,
            market_type=MarketType.BINARY,
            kalshi_ticker="KXAAAGASMAXTX-25DEC31-3",
            description="Texas Gas Price >= $3 (Volume: 33,977)",
            enable_spatial_arb=True,
            min_liquidity_usd=10000.0
        ))

        self.markets.append(MarketDefinition(
            name="Real Wage Growth Above 0%",
            category=MarketCategory.ECONOMICS,
            market_type=MarketType.BINARY,
            kalshi_ticker="KXREALWAGES-25",
            description="Real Wage Growth Above 0% in 2025 (Volume: 22,171)",
            enable_spatial_arb=True,
            min_liquidity_usd=10000.0
        ))

        # ====================================================================
        # MORE CRYPTO MARKETS
        # ====================================================================

        self.markets.append(MarketDefinition(
            name="Ethereum >= $5000 Dec 2025",
            category=MarketCategory.FINANCE,
            market_type=MarketType.BINARY,
            kalshi_ticker="KXETHMAXM-25DEC01-5000",
            description="Ethereum >= $5000 Dec 2025 (Volume: 2,265)",
            enable_spatial_arb=True,
            min_liquidity_usd=2000.0
        ))

        self.markets.append(MarketDefinition(
            name="OpenSea Token Launch Jan 2026",
            category=MarketCategory.FINANCE,
            market_type=MarketType.BINARY,
            kalshi_ticker="KXTOKENLAUNCHOPENSEA-26JAN01",
            description="OpenSea Token Launch Jan 2026 (Volume: 7,340)",
            enable_spatial_arb=True,
            min_liquidity_usd=5000.0
        ))

        self.markets.append(MarketDefinition(
            name="Utah BTC Reserve 2026",
            category=MarketCategory.POLITICS_US,
            market_type=MarketType.BINARY,
            kalshi_ticker="KXBTCRESERVESTATES-26-UT",
            description="Utah BTC Reserve 2026 (Volume: 14,723)",
            enable_spatial_arb=True,
            min_liquidity_usd=5000.0
        ))

        # All markets verified with actual volume data from Kalshi API
        # Query date: November 17, 2025

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
