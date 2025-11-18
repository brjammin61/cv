"""
Market Registry Configuration - POLITICS & ECONOMICS ONLY

Oracle's competitive edge is in political prediction markets where behavioral
biases (partisan wishful thinking, shy voter effect, favorite-longshot bias)
create exploitable inefficiencies.

We AVOID crypto/stock markets - those are too efficient and we'd be competing
against professional arbitrage bots. Our strategies work on markets where
humans bet emotionally, not rationally.

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
    enable_bias_correction: bool = True  # Default TRUE for political markets
    enable_spatial_arb: bool = True
    enable_dutch_book: bool = False
    enable_rfr_analysis: bool = False


class MarketRegistry:
    """
    Registry of REAL markets to monitor - POLITICS & ECONOMICS ONLY.

    Our edge is in markets where behavioral biases dominate, not efficient
    price-tracking markets. We beat partisan traders, not Renaissance.
    """

    def __init__(self):
        """Initialize the market registry with politics/economics markets."""
        self.markets: List[MarketDefinition] = []
        self._load_politics_economics_markets()

    def _load_politics_economics_markets(self):
        """
        Load high-quality politics and economics markets.

        FOCUS AREAS:
        - 2026 Midterm Elections (House/Senate control, key races)
        - Fed Rate Decisions (FOMC meetings)
        - Economic Indicators (CPI, Jobs, GDP)
        - Political Events (Shutdowns, legislation, confirmations)
        """

        # ====================================================================
        # 2026 MIDTERM ELECTIONS - HIGHEST PRIORITY
        # These markets have massive behavioral biases (partisan wishful thinking)
        # and are perfect for Shy Voter, Favorite-Longshot, and Bias Correction
        # ====================================================================

        self.markets.append(MarketDefinition(
            name="House Control 2026 - Democrat",
            category=MarketCategory.POLITICS_US,
            market_type=MarketType.BINARY,
            kalshi_ticker="CONGRESS-2026H-D",  # Placeholder - update with real ticker
            description="Democrats win House majority in 2026 midterms (High volume expected)",
            resolution_date=date(2026, 11, 3),
            enable_bias_correction=True,
            enable_spatial_arb=True,
            min_liquidity_usd=50000.0
        ))

        self.markets.append(MarketDefinition(
            name="Senate Control 2026 - Republican",
            category=MarketCategory.POLITICS_US,
            market_type=MarketType.BINARY,
            kalshi_ticker="CONGRESS-2026S-R",  # Placeholder - update with real ticker
            description="Republicans win Senate majority in 2026 midterms (High volume expected)",
            resolution_date=date(2026, 11, 3),
            enable_bias_correction=True,
            enable_spatial_arb=True,
            min_liquidity_usd=50000.0
        ))

        # Key Senate Races - Competitive states where polling biases matter most

        self.markets.append(MarketDefinition(
            name="Arizona Senate 2026 - Democrat",
            category=MarketCategory.POLITICS_US,
            market_type=MarketType.BINARY,
            kalshi_ticker="SENATEAZ-26-D",  # Placeholder
            description="Democrat wins Arizona Senate seat 2026",
            resolution_date=date(2026, 11, 3),
            enable_bias_correction=True,
            enable_spatial_arb=True,
            min_liquidity_usd=5000.0
        ))

        self.markets.append(MarketDefinition(
            name="Pennsylvania Senate 2026 - Democrat",
            category=MarketCategory.POLITICS_US,
            market_type=MarketType.BINARY,
            kalshi_ticker="SENATEPA-26-D",  # Placeholder
            description="Democrat wins Pennsylvania Senate seat 2026",
            resolution_date=date(2026, 11, 3),
            enable_bias_correction=True,
            enable_spatial_arb=True,
            min_liquidity_usd=5000.0
        ))

        self.markets.append(MarketDefinition(
            name="Georgia Senate 2026 - Democrat",
            category=MarketCategory.POLITICS_US,
            market_type=MarketType.BINARY,
            kalshi_ticker="SENATEGA-26-D",  # Placeholder
            description="Democrat wins Georgia Senate seat 2026",
            resolution_date=date(2026, 11, 3),
            enable_bias_correction=True,
            enable_spatial_arb=True,
            min_liquidity_usd=5000.0
        ))

        # Key House Races - Swing districts

        self.markets.append(MarketDefinition(
            name="House VA-7 Democrat",
            category=MarketCategory.POLITICS_US,
            market_type=MarketType.BINARY,
            kalshi_ticker="HOUSEVA7-26-D",
            description="House Virginia 7th District Democrat wins 2026",
            resolution_date=date(2026, 11, 3),
            enable_bias_correction=True,
            enable_spatial_arb=True,
            min_liquidity_usd=1000.0
        ))

        self.markets.append(MarketDefinition(
            name="House CA-22 Democrat",
            category=MarketCategory.POLITICS_US,
            market_type=MarketType.BINARY,
            kalshi_ticker="HOUSECA22-26-D",  # Placeholder
            description="House California 22nd District Democrat wins 2026",
            resolution_date=date(2026, 11, 3),
            enable_bias_correction=True,
            enable_spatial_arb=True,
            min_liquidity_usd=2000.0
        ))

        # ====================================================================
        # FEDERAL RESERVE & MONETARY POLICY
        # Markets driven by Fed watchers, economists - less partisan bias but
        # still behavioral (overreaction to news, favorite-longshot)
        # ====================================================================

        self.markets.append(MarketDefinition(
            name="Fed Rate Dec 2025 - Cut 25bp",
            category=MarketCategory.ECONOMICS,
            market_type=MarketType.BINARY,
            kalshi_ticker="FED-25DEC-B4.25",  # Placeholder
            description="Fed cuts rates by 25bp in December 2025 FOMC meeting",
            resolution_date=date(2025, 12, 18),
            enable_bias_correction=False,  # Less partisan bias
            enable_spatial_arb=True,
            enable_rfr_analysis=True,
            min_liquidity_usd=10000.0
        ))

        self.markets.append(MarketDefinition(
            name="Fed Rate Mar 2026 - Above 4.0%",
            category=MarketCategory.ECONOMICS,
            market_type=MarketType.BINARY,
            kalshi_ticker="FED-26MAR-T4.00",  # Placeholder
            description="Fed Funds Rate above 4.0% after March 2026 FOMC",
            resolution_date=date(2026, 3, 20),
            enable_bias_correction=False,
            enable_spatial_arb=True,
            enable_rfr_analysis=True,
            min_liquidity_usd=10000.0
        ))

        # ====================================================================
        # ECONOMIC INDICATORS
        # These resolve based on hard data, but markets can misprice due to
        # recency bias, overreaction to monthly noise, false liquidity
        # ====================================================================

        self.markets.append(MarketDefinition(
            name="CPI YoY Dec 2025 - Above 2.5%",
            category=MarketCategory.ECONOMICS,
            market_type=MarketType.BINARY,
            kalshi_ticker="CPIYOY-25DEC-T2.5",  # Placeholder
            description="CPI Year-over-Year inflation above 2.5% in December 2025",
            resolution_date=date(2026, 1, 15),  # CPI releases ~mid-month
            enable_bias_correction=False,
            enable_spatial_arb=True,
            min_liquidity_usd=5000.0
        ))

        self.markets.append(MarketDefinition(
            name="Unemployment Jan 2026 - Below 4.0%",
            category=MarketCategory.ECONOMICS,
            market_type=MarketType.BINARY,
            kalshi_ticker="UNEMP-26JAN-B4.0",  # Placeholder
            description="Unemployment rate below 4.0% in January 2026 jobs report",
            resolution_date=date(2026, 2, 7),  # Jobs report first Friday
            enable_bias_correction=False,
            enable_spatial_arb=True,
            min_liquidity_usd=5000.0
        ))

        self.markets.append(MarketDefinition(
            name="Real Wage Growth 2025 - Above 0%",
            category=MarketCategory.ECONOMICS,
            market_type=MarketType.BINARY,
            kalshi_ticker="KXREALWAGES-25",
            description="Real wage growth positive in 2025 (Verified active)",
            resolution_date=date(2026, 1, 31),
            enable_spatial_arb=True,
            min_liquidity_usd=10000.0
        ))

        # ====================================================================
        # POLITICAL EVENTS & GOVERNANCE
        # High behavioral bias - partisans bet on what they want, not what's likely
        # Perfect for bias correction and false liquidity bait strategies
        # ====================================================================

        self.markets.append(MarketDefinition(
            name="Government Shutdown 2026",
            category=MarketCategory.POLITICS_US,
            market_type=MarketType.BINARY,
            kalshi_ticker="SHUTDOWN-26",  # Placeholder
            description="Federal government shutdown occurs in 2026",
            resolution_date=date(2026, 12, 31),
            enable_bias_correction=True,
            enable_spatial_arb=True,
            min_liquidity_usd=5000.0
        ))

        self.markets.append(MarketDefinition(
            name="DC Federalization by Jan 2027",
            category=MarketCategory.POLITICS_US,
            market_type=MarketType.BINARY,
            kalshi_ticker="KXFEDDC-27JAN-FEDDC",
            description="DC Federalization by Jan 2027 (Verified active: Vol 32,835)",
            resolution_date=date(2027, 1, 1),
            enable_bias_correction=True,
            enable_spatial_arb=True,
            min_liquidity_usd=10000.0
        ))

        self.markets.append(MarketDefinition(
            name="Supreme Court Expansion 2026",
            category=MarketCategory.POLITICS_US,
            market_type=MarketType.BINARY,
            kalshi_ticker="SCOTUS-EXPAND-26",  # Placeholder
            description="Supreme Court expanded beyond 9 justices by end of 2026",
            resolution_date=date(2026, 12, 31),
            enable_bias_correction=True,
            enable_spatial_arb=True,
            min_liquidity_usd=5000.0
        ))

        # ====================================================================
        # NOTES ON MARKET SELECTION
        # ====================================================================
        #
        # WHY THESE MARKETS?
        # - Behavioral inefficiencies: Partisans bet with hearts not heads
        # - Our strategies designed for this: Shy Voter, Favorite-Longshot
        # - Avoid efficient markets: No crypto/stocks (those just track prices)
        # - High enough volume for meaningful execution
        # - Clear resolution criteria (official data, election results)
        #
        # TO UPDATE TICKERS:
        # 1. SSH to droplet: ssh root@159.223.201.145
        # 2. Run: cd /opt/oracle && python3 find_active_markets.py
        # 3. Replace placeholder tickers with real ones
        # 4. Update min_liquidity_usd based on actual volumes
        #
        # ====================================================================

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
    print("POLITICS & ECONOMICS MARKET REGISTRY")
    print("=" * 80)
    print("\n🎯 Our Edge: Behavioral biases in political prediction markets")
    print("❌ Avoid: Efficient crypto/stock markets (no behavioral edge)")

    all_markets = registry.get_all_markets()
    print(f"\n📊 Total Active Markets: {len(all_markets)}")

    print("\n" + "=" * 80)
    print("MARKETS BY CATEGORY")
    print("=" * 80)

    for category in [MarketCategory.POLITICS_US, MarketCategory.ECONOMICS]:
        markets = registry.get_markets_by_category(category)
        if markets:
            print(f"\n{category.value.upper()}: {len(markets)} markets")
            for m in markets:
                ticker = m.kalshi_ticker or "TBD"
                print(f"  - {ticker:30} {m.name}")

    print("\n" + "=" * 80)
    print("STRATEGY ENABLEMENT")
    print("=" * 80)

    print(f"\n🎯 Bias Correction: {len(registry.get_bias_correction_markets())} markets")
    print(f"🔄 Spatial Arbitrage: {len(registry.get_spatial_arb_markets())} markets")
    print(f"📊 Dutch Book: {len(registry.get_dutch_book_markets())} markets")

    print("\n" + "=" * 80)
    print("✅ Configuration focused on markets where behavioral biases create edge")
    print("=" * 80)
