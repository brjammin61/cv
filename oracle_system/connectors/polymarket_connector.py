"""
Polymarket Exchange Connector

Handles connections to the Polymarket CLOB API for market data retrieval.

⚠️ PRODUCTION NOTE:
The current implementation uses simulated data for demonstration.
To use real Polymarket data, uncomment the real API sections and provide
a valid Ethereum private key in config/api_keys.py
"""

import logging
import random
from typing import Optional, Dict, List
from datetime import datetime

from .data_models import OrderBookData, MarketData, Exchange

logger = logging.getLogger(__name__)


class PolymarketConnector:
    """
    Connector for Polymarket prediction market exchange.

    This class handles authentication and data retrieval from Polymarket's CLOB.
    """

    def __init__(
        self,
        private_key: Optional[str] = None,
        clob_api_url: str = "https://clob.polymarket.com",
        polygon_rpc: Optional[str] = None,
        simulate_data: bool = True
    ):
        """
        Initialize Polymarket connector.

        Args:
            private_key (str, optional): Ethereum wallet private key
            clob_api_url (str): Polymarket CLOB API endpoint
            polygon_rpc (str, optional): Polygon RPC endpoint
            simulate_data (bool): Use simulated data instead of real API
        """
        self.private_key = private_key
        self.clob_api_url = clob_api_url
        self.polygon_rpc = polygon_rpc
        self.simulate_data = simulate_data

        self.client = None
        self.connected = False

        if not simulate_data:
            self._initialize_real_client()
        else:
            logger.info("Polymarket connector initialized in SIMULATION mode")
            self.connected = True

    def _initialize_real_client(self):
        """
        Initialize the real Polymarket CLOB client.

        PRODUCTION IMPLEMENTATION:
        Uncomment this code and provide real credentials to use live data.
        """
        # try:
        #     from py_clob_client.client import ClobClient
        #     from py_clob_client.clob_types import ApiCreds
        #
        #     # Initialize client
        #     self.client = ClobClient(
        #         host=self.clob_api_url,
        #         key=self.private_key,
        #         chain_id=137  # Polygon mainnet
        #     )
        #
        #     # Derive API credentials from private key
        #     self.client.set_api_creds(
        #         self.client.create_or_derive_api_creds()
        #     )
        #
        #     self.connected = True
        #     logger.info("✅ Connected to Polymarket CLOB")
        # except Exception as e:
        #     logger.error(f"❌ Failed to connect to Polymarket: {e}")
        #     self.connected = False

        logger.warning("Real Polymarket API not implemented yet. Using simulation mode.")
        self.simulate_data = True
        self.connected = True

    def get_order_book(
        self,
        condition_id: str,
        market_name: str = None,
        token_id: Optional[str] = None
    ) -> Optional[OrderBookData]:
        """
        Fetch current order book for a market.

        Args:
            condition_id (str): Polymarket condition ID (market identifier)
            market_name (str, optional): Human-readable market name
            token_id (str, optional): Specific token ID (for YES/NO tokens)

        Returns:
            OrderBookData or None if fetch fails
        """
        if not self.connected:
            logger.error("Not connected to Polymarket")
            return None

        if self.simulate_data:
            return self._simulate_order_book(condition_id, market_name)

        # PRODUCTION IMPLEMENTATION:
        # try:
        #     # Fetch order book from CLOB
        #     order_book = self.client.get_order_book(token_id or condition_id)
        #
        #     # Parse bids and asks
        #     bids = order_book.get('bids', [])
        #     asks = order_book.get('asks', [])
        #
        #     best_bid = float(bids[0]['price']) if bids else 0.0
        #     best_ask = float(asks[0]['price']) if asks else 1.0
        #     bid_size = float(bids[0]['size']) if bids else 0.0
        #     ask_size = float(asks[0]['size']) if asks else 0.0
        #
        #     return OrderBookData(
        #         exchange=Exchange.POLYMARKET,
        #         market_id=condition_id,
        #         market_name=market_name or condition_id[:16] + "...",
        #         best_bid=best_bid,
        #         best_ask=best_ask,
        #         bid_size=bid_size,
        #         ask_size=ask_size,
        #     )
        # except Exception as e:
        #     logger.error(f"Failed to fetch Polymarket order book for {condition_id}: {e}")
        #     return None

    def _simulate_order_book(self, condition_id: str, market_name: str = None) -> OrderBookData:
        """Generate simulated order book data for testing."""
        # Generate realistic-looking data
        base_price = random.uniform(0.30, 0.70)
        spread = random.uniform(0.015, 0.035)  # Polymarket typically has wider spreads

        bid = round(base_price - spread / 2, 3)
        ask = round(base_price + spread / 2, 3)

        return OrderBookData(
            exchange=Exchange.POLYMARKET,
            market_id=condition_id,
            market_name=market_name or f"Market {condition_id[:8]}...",
            best_bid=bid,
            best_ask=ask,
            bid_size=random.uniform(100, 2000),
            ask_size=random.uniform(100, 2000),
            timestamp=datetime.now()
        )

    def get_market_data(self, condition_id: str) -> Optional[MarketData]:
        """
        Fetch complete market data including order book.

        Args:
            condition_id (str): Polymarket condition ID

        Returns:
            MarketData or None if fetch fails
        """
        if not self.connected:
            logger.error("Not connected to Polymarket")
            return None

        if self.simulate_data:
            return self._simulate_market_data(condition_id)

        # PRODUCTION IMPLEMENTATION:
        # try:
        #     # Fetch market info
        #     market = self.client.get_market(condition_id)
        #     order_book = self.get_order_book(
        #         condition_id,
        #         market.get('question'),
        #         market.get('tokens', [{}])[0].get('token_id')
        #     )
        #
        #     return MarketData(
        #         exchange=Exchange.POLYMARKET,
        #         market_id=condition_id,
        #         market_name=market.get('question', condition_id),
        #         description=market.get('description'),
        #         order_book=order_book,
        #         last_price=float(market.get('outcomePrices', [0.5])[0]),
        #         volume_24h=float(market.get('volume24hr', 0)),
        #         open_interest=float(market.get('liquidity', 0)),
        #         is_active=market.get('active', True),
        #         resolution_date=None  # Polymarket doesn't always provide this
        #     )
        # except Exception as e:
        #     logger.error(f"Failed to fetch Polymarket market data for {condition_id}: {e}")
        #     return None

    def _simulate_market_data(self, condition_id: str) -> MarketData:
        """Generate simulated market data for testing."""
        order_book = self._simulate_order_book(condition_id)

        return MarketData(
            exchange=Exchange.POLYMARKET,
            market_id=condition_id,
            market_name=f"Market {condition_id[:8]}...",
            description=f"Simulated market data for {condition_id}",
            order_book=order_book,
            last_price=order_book.mid_price,
            volume_24h=random.uniform(5000, 50000),
            open_interest=random.uniform(20000, 200000),
            is_active=True,
            last_updated=datetime.now()
        )

    def get_markets(self, limit: int = 20) -> List[Dict]:
        """
        Fetch list of available markets.

        Args:
            limit (int): Maximum number of markets to return

        Returns:
            List of market dictionaries
        """
        if not self.connected:
            logger.error("Not connected to Polymarket")
            return []

        if self.simulate_data:
            return self._simulate_markets_list(limit)

        # PRODUCTION IMPLEMENTATION:
        # try:
        #     response = self.client.get_markets(limit=limit)
        #     return response
        # except Exception as e:
        #     logger.error(f"Failed to fetch Polymarket markets: {e}")
        #     return []

    def _simulate_markets_list(self, limit: int = 20) -> List[Dict]:
        """Generate simulated markets list."""
        markets = [
            {
                "condition_id": "0x1234...abcd",
                "question": "2028 Presidential Election",
                "category": "politics"
            },
            {
                "condition_id": "0x5678...efgh",
                "question": "Fed Rate Cut Dec 2026",
                "category": "economics"
            },
            {
                "condition_id": "0x9abc...ijkl",
                "question": "Bitcoin Above $100k in 2026",
                "category": "finance"
            },
        ]

        return markets[:limit]

    def get_simplified_markets(self) -> List[Dict]:
        """
        Get simplified market data optimized for the dashboard.

        Returns:
            List of simplified market dictionaries
        """
        markets = self.get_markets()
        simplified = []

        for market in markets:
            condition_id = market.get('condition_id', market.get('id', 'unknown'))
            order_book = self.get_order_book(
                condition_id,
                market.get('question', market.get('name', 'Unknown Market'))
            )

            if order_book:
                simplified.append({
                    'id': condition_id,
                    'name': order_book.market_name,
                    'bid': order_book.best_bid,
                    'ask': order_book.best_ask,
                    'mid': order_book.mid_price,
                    'spread': order_book.spread
                })

        return simplified

    def close(self):
        """Close connection to Polymarket."""
        if self.client:
            # Close real client if applicable
            pass
        self.connected = False
        logger.info("Disconnected from Polymarket")


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 80)
    print("Polymarket Connector - Example Usage (Simulation Mode)")
    print("=" * 80)

    # Initialize connector in simulation mode
    connector = PolymarketConnector(simulate_data=True)

    # Fetch order book
    print("\n[1] Fetching order book...")
    order_book = connector.get_order_book("0x1234...abcd", "2028 Presidential Election")
    if order_book:
        print(f"  Best Bid: {order_book.best_bid:.3f}")
        print(f"  Best Ask: {order_book.best_ask:.3f}")
        print(f"  Mid Price: {order_book.mid_price:.3f}")
        print(f"  Spread: {order_book.spread:.4f} ({order_book.spread_bps:.1f} bps)")

    # Fetch complete market data
    print("\n[2] Fetching complete market data...")
    market_data = connector.get_market_data("0x5678...efgh")
    if market_data:
        print(f"  Market: {market_data.market_name}")
        print(f"  Last Price: {market_data.last_price:.3f}")
        print(f"  24h Volume: ${market_data.volume_24h:,.0f}")

    # List markets
    print("\n[3] Listing available markets...")
    markets = connector.get_markets()
    for market in markets:
        print(f"  - {market['question']}")

    # Get simplified markets for dashboard
    print("\n[4] Getting simplified market data for dashboard...")
    simplified = connector.get_simplified_markets()
    for market in simplified:
        print(f"  - {market['name']}: Bid={market['bid']:.3f}, Ask={market['ask']:.3f}")

    connector.close()
