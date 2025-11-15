"""
Data Models for Market Data

Standardized data structures for market information from different exchanges.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict
from enum import Enum


class Exchange(Enum):
    """Exchange identifiers."""
    KALSHI = "kalshi"
    POLYMARKET = "polymarket"


@dataclass
class OrderBookData:
    """Standardized order book data."""

    # Exchange information
    exchange: Exchange
    market_id: str
    market_name: str

    # Order book state
    best_bid: float
    best_ask: float
    bid_size: float = 0.0
    ask_size: float = 0.0

    # Calculated fields
    mid_price: float = field(init=False)
    spread: float = field(init=False)
    spread_bps: float = field(init=False)

    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    is_stale: bool = False

    def __post_init__(self):
        """Calculate derived fields."""
        self.mid_price = (self.best_bid + self.best_ask) / 2
        self.spread = self.best_ask - self.best_bid
        self.spread_bps = (self.spread / self.mid_price * 10000) if self.mid_price > 0 else 0

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'exchange': self.exchange.value,
            'market_id': self.market_id,
            'market_name': self.market_name,
            'best_bid': self.best_bid,
            'best_ask': self.best_ask,
            'bid_size': self.bid_size,
            'ask_size': self.ask_size,
            'mid_price': self.mid_price,
            'spread': self.spread,
            'spread_bps': self.spread_bps,
            'timestamp': self.timestamp.isoformat(),
            'is_stale': self.is_stale
        }


@dataclass
class MarketData:
    """Complete market information."""

    # Exchange information
    exchange: Exchange
    market_id: str
    market_name: str
    description: Optional[str] = None

    # Market state
    order_book: Optional[OrderBookData] = None
    last_price: Optional[float] = None
    volume_24h: float = 0.0
    open_interest: float = 0.0

    # Market characteristics
    is_active: bool = True
    min_tick_size: float = 0.01
    resolution_date: Optional[datetime] = None

    # Metadata
    last_updated: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'exchange': self.exchange.value,
            'market_id': self.market_id,
            'market_name': self.market_name,
            'description': self.description,
            'order_book': self.order_book.to_dict() if self.order_book else None,
            'last_price': self.last_price,
            'volume_24h': self.volume_24h,
            'open_interest': self.open_interest,
            'is_active': self.is_active,
            'min_tick_size': self.min_tick_size,
            'resolution_date': self.resolution_date.isoformat() if self.resolution_date else None,
            'last_updated': self.last_updated.isoformat()
        }


@dataclass
class TradeData:
    """Individual trade information."""

    # Exchange information
    exchange: Exchange
    market_id: str

    # Trade details
    price: float
    size: float
    side: str  # "buy" or "sell"

    # Metadata
    trade_id: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'exchange': self.exchange.value,
            'market_id': self.market_id,
            'price': self.price,
            'size': self.size,
            'side': self.side,
            'trade_id': self.trade_id,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class PollingData:
    """Polling data for bias correction."""

    # Poll information
    poll_name: str
    pollster: str

    # Key data points
    self_preference: float  # "Who will you vote for?"
    neighbor_preference: Optional[float] = None  # "Who will your neighbors vote for?"

    # Metadata
    sample_size: int = 0
    margin_of_error: Optional[float] = None
    poll_date: Optional[datetime] = None
    publication_date: datetime = field(default_factory=datetime.now)

    # Quality indicators
    is_reliable: bool = True
    reliability_score: float = 1.0

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'poll_name': self.poll_name,
            'pollster': self.pollster,
            'self_preference': self.self_preference,
            'neighbor_preference': self.neighbor_preference,
            'sample_size': self.sample_size,
            'margin_of_error': self.margin_of_error,
            'poll_date': self.poll_date.isoformat() if self.poll_date else None,
            'publication_date': self.publication_date.isoformat(),
            'is_reliable': self.is_reliable,
            'reliability_score': self.reliability_score
        }


# Example usage
if __name__ == "__main__":
    # Create sample order book data
    kalshi_book = OrderBookData(
        exchange=Exchange.KALSHI,
        market_id="PREZ-28",
        market_name="2028 Presidential Election",
        best_bid=0.50,
        best_ask=0.51,
        bid_size=1000,
        ask_size=800
    )

    print("Order Book Data:")
    print(f"  Exchange: {kalshi_book.exchange.value}")
    print(f"  Market: {kalshi_book.market_name}")
    print(f"  Best Bid: {kalshi_book.best_bid:.3f}")
    print(f"  Best Ask: {kalshi_book.best_ask:.3f}")
    print(f"  Mid Price: {kalshi_book.mid_price:.3f}")
    print(f"  Spread: {kalshi_book.spread:.4f} ({kalshi_book.spread_bps:.1f} bps)")

    # Convert to dict
    print("\nAs Dictionary:")
    import json
    print(json.dumps(kalshi_book.to_dict(), indent=2))
