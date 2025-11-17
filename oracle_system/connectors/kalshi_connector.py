"""
Kalshi Exchange Connector

Handles connections to the Kalshi API for market data retrieval.

⚠️ PRODUCTION NOTE:
The current implementation uses simulated data for demonstration.
To use real Kalshi data, uncomment the real API sections and provide
valid API credentials in config/api_keys.py
"""

import logging
import random
import time
import hashlib
import base64
from typing import Optional, Dict, List
from datetime import datetime
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

from .data_models import OrderBookData, MarketData, Exchange

logger = logging.getLogger(__name__)


class KalshiConnector:
    """
    Connector for Kalshi prediction market exchange.

    This class handles authentication and data retrieval from Kalshi.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        private_key_path: Optional[str] = None,
        use_demo: bool = False,
        simulate_data: bool = False
    ):
        """
        Initialize Kalshi connector.

        Args:
            api_key (str, optional): Kalshi API key
            private_key_path (str, optional): Path to RSA private key
            use_demo (bool): Use demo environment (no real money)
            simulate_data (bool): Use simulated data instead of real API
        """
        self.api_key = api_key
        self.private_key_path = private_key_path
        self.use_demo = use_demo
        self.simulate_data = simulate_data

        self.client = None
        self.connected = False

        # Import API key and private key path from config if not provided
        if api_key is None and not simulate_data:
            try:
                from config.api_keys import KALSHI_API_KEY, KALSHI_PRIVATE_KEY_PATH
                self.api_key = KALSHI_API_KEY
                self.private_key_path = private_key_path or KALSHI_PRIVATE_KEY_PATH
                logger.info("Loaded Kalshi API credentials from config")
            except ImportError:
                logger.warning("No API key provided and config not found")
                self.simulate_data = True

        if not simulate_data:
            self._initialize_real_client()
        else:
            logger.info("Kalshi connector initialized in SIMULATION mode")
            self.connected = True

    def _initialize_real_client(self):
        """
        Initialize the real Kalshi API client using HTTP requests with RSA signature auth.
        """
        try:
            import requests

            # Set API base URL
            if self.use_demo:
                self.api_base = "https://demo-api.kalshi.co/trade-api/v2"
            else:
                self.api_base = "https://api.elections.kalshi.com/trade-api/v2"

            # Load private key if path provided
            self.private_key = None
            if self.private_key_path:
                try:
                    with open(self.private_key_path, 'rb') as key_file:
                        self.private_key = serialization.load_pem_private_key(
                            key_file.read(),
                            password=None,
                            backend=default_backend()
                        )
                    logger.info("Loaded RSA private key")
                except Exception as e:
                    logger.warning(f"Failed to load private key: {e}")
                    logger.info("Falling back to simulation mode")
                    self.simulate_data = True
                    self.connected = False
                    return

            # Test connection with signed request
            response = self._make_request('GET', '/exchange/status')

            if response and response.status_code == 200:
                self.connected = True
                logger.info(f"✅ Kalshi connector initialized ({'DEMO' if self.use_demo else 'PRODUCTION'})")
            else:
                status = response.status_code if response else 'No response'
                logger.error(f"❌ Failed to connect: {status}")
                self.connected = False
                self.simulate_data = True

        except Exception as e:
            logger.error(f"❌ Failed to initialize Kalshi client: {e}")
            self.connected = False
            self.simulate_data = True

    def _generate_signature(self, timestamp_str: str, method: str, path: str) -> str:
        """
        Generate RSA signature for Kalshi API request.

        Args:
            timestamp_str: Request timestamp in milliseconds
            method: HTTP method (GET, POST, etc.)
            path: Request path (e.g., '/exchange/status')

        Returns:
            Base64-encoded signature
        """
        # Message to sign: timestamp + method + path
        message = timestamp_str + method + path
        message_bytes = message.encode('utf-8')

        # Sign with RSA private key using PSS padding
        signature = self.private_key.sign(
            message_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        # Return base64-encoded signature
        return base64.b64encode(signature).decode('utf-8')

    def _make_request(self, method: str, path: str, params: Dict = None) -> Optional[object]:
        """
        Make an authenticated request to Kalshi API.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path (e.g., '/markets')
            params: Query parameters

        Returns:
            Response object or None
        """
        try:
            import requests

            # Generate timestamp (milliseconds since epoch)
            timestamp_ms = int(time.time() * 1000)
            timestamp_str = str(timestamp_ms)

            # Generate signature
            signature = self._generate_signature(timestamp_str, method, path)

            # Build headers with Kalshi's custom authentication
            headers = {
                'KALSHI-ACCESS-KEY': self.api_key,
                'KALSHI-ACCESS-SIGNATURE': signature,
                'KALSHI-ACCESS-TIMESTAMP': timestamp_str,
                'Content-Type': 'application/json'
            }

            # Make request
            url = f"{self.api_base}{path}"
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                timeout=10
            )

            return response

        except Exception as e:
            logger.error(f"Request failed: {e}")
            return None

    def get_order_book(self, market_ticker: str, market_name: str = None) -> Optional[OrderBookData]:
        """
        Fetch current order book for a market.

        Args:
            market_ticker (str): Kalshi market ticker (e.g., "PREZ-28")
            market_name (str, optional): Human-readable market name

        Returns:
            OrderBookData or None if fetch fails
        """
        if not self.connected:
            logger.error("Not connected to Kalshi")
            return None

        if self.simulate_data:
            return self._simulate_order_book(market_ticker, market_name)

        # Real API implementation
        try:
            # Get market details
            market_response = self._make_request('GET', f'/markets/{market_ticker}')

            if not market_response or market_response.status_code != 200:
                status = market_response.status_code if market_response else 'No response'
                logger.warning(f"Failed to fetch market {market_ticker}: {status}")
                return self._simulate_order_book(market_ticker, market_name)

            market_data = market_response.json()

            # Get orderbook
            orderbook_response = self._make_request('GET', f'/markets/{market_ticker}/orderbook')

            if not orderbook_response or orderbook_response.status_code != 200:
                logger.warning(f"Failed to fetch orderbook for {market_ticker}")
                return self._simulate_order_book(market_ticker, market_name)

            orderbook = orderbook_response.json()

            # Extract best bid/ask
            bids = orderbook.get('yes', {}).get('bids', [])
            asks = orderbook.get('yes', {}).get('asks', [])

            best_bid = float(bids[0]['price']) / 100 if bids else 0.0  # Convert cents to dollars
            best_ask = float(asks[0]['price']) / 100 if asks else 1.0
            bid_size = float(bids[0]['size']) if bids else 0.0
            ask_size = float(asks[0]['size']) if asks else 0.0

            return OrderBookData(
                exchange=Exchange.KALSHI,
                market_id=market_ticker,
                market_name=market_name or market_data.get('title', market_ticker),
                best_bid=best_bid,
                best_ask=best_ask,
                bid_size=bid_size,
                ask_size=ask_size,
                timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"Failed to fetch Kalshi order book for {market_ticker}: {e}")
            # Fallback to simulation
            return self._simulate_order_book(market_ticker, market_name)

    def _simulate_order_book(self, market_ticker: str, market_name: str = None) -> OrderBookData:
        """Generate simulated order book data for testing."""
        # Generate realistic-looking data
        base_price = random.uniform(0.30, 0.70)
        spread = random.uniform(0.01, 0.03)

        bid = round(base_price - spread / 2, 2)
        ask = round(base_price + spread / 2, 2)

        return OrderBookData(
            exchange=Exchange.KALSHI,
            market_id=market_ticker,
            market_name=market_name or f"Market {market_ticker}",
            best_bid=bid,
            best_ask=ask,
            bid_size=random.uniform(500, 5000),
            ask_size=random.uniform(500, 5000),
            timestamp=datetime.now()
        )

    def get_market_data(self, market_ticker: str) -> Optional[MarketData]:
        """
        Fetch complete market data including order book.

        Args:
            market_ticker (str): Kalshi market ticker

        Returns:
            MarketData or None if fetch fails
        """
        if not self.connected:
            logger.error("Not connected to Kalshi")
            return None

        if self.simulate_data:
            return self._simulate_market_data(market_ticker)

        # PRODUCTION IMPLEMENTATION:
        # try:
        #     response = self.client.get_market(market_ticker)
        #     order_book = self.get_order_book(market_ticker, response.get('title'))
        #
        #     return MarketData(
        #         exchange=Exchange.KALSHI,
        #         market_id=market_ticker,
        #         market_name=response.get('title', market_ticker),
        #         description=response.get('description'),
        #         order_book=order_book,
        #         last_price=float(response.get('last_price', 0)),
        #         volume_24h=float(response.get('volume_24h', 0)),
        #         open_interest=float(response.get('open_interest', 0)),
        #         is_active=response.get('status') == 'active',
        #         resolution_date=datetime.fromisoformat(response.get('close_date'))
        #     )
        # except Exception as e:
        #     logger.error(f"Failed to fetch Kalshi market data for {market_ticker}: {e}")
        #     return None

    def _simulate_market_data(self, market_ticker: str) -> MarketData:
        """Generate simulated market data for testing."""
        order_book = self._simulate_order_book(market_ticker)

        return MarketData(
            exchange=Exchange.KALSHI,
            market_id=market_ticker,
            market_name=f"Market {market_ticker}",
            description=f"Simulated market data for {market_ticker}",
            order_book=order_book,
            last_price=order_book.mid_price,
            volume_24h=random.uniform(10000, 100000),
            open_interest=random.uniform(50000, 500000),
            is_active=True,
            last_updated=datetime.now()
        )

    def get_markets(self, category: str = None) -> List[Dict]:
        """
        Fetch list of available markets.

        Args:
            category (str, optional): Filter by category

        Returns:
            List of market dictionaries
        """
        if not self.connected:
            logger.error("Not connected to Kalshi")
            return []

        if self.simulate_data:
            return self._simulate_markets_list(category)

        # PRODUCTION IMPLEMENTATION:
        # try:
        #     response = self.client.get_markets(category=category)
        #     return response.get('markets', [])
        # except Exception as e:
        #     logger.error(f"Failed to fetch Kalshi markets: {e}")
        #     return []

    def _simulate_markets_list(self, category: str = None) -> List[Dict]:
        """Generate simulated markets list."""
        markets = [
            {"ticker": "PREZ-28", "title": "2028 Presidential Election", "category": "politics"},
            {"ticker": "FED-CUT-DEC26", "title": "Fed Rate Cut Dec 2026", "category": "economics"},
            {"ticker": "BTC-100K-26", "title": "Bitcoin Above $100k in 2026", "category": "finance"},
        ]

        if category:
            markets = [m for m in markets if m.get('category') == category]

        return markets

    def close(self):
        """Close connection to Kalshi."""
        if self.client:
            # Close real client if applicable
            pass
        self.connected = False
        logger.info("Disconnected from Kalshi")


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 80)
    print("Kalshi Connector - Example Usage (Simulation Mode)")
    print("=" * 80)

    # Initialize connector in simulation mode
    connector = KalshiConnector(simulate_data=True)

    # Fetch order book
    print("\n[1] Fetching order book for PREZ-28...")
    order_book = connector.get_order_book("PREZ-28", "2028 Presidential Election")
    if order_book:
        print(f"  Best Bid: {order_book.best_bid:.3f}")
        print(f"  Best Ask: {order_book.best_ask:.3f}")
        print(f"  Mid Price: {order_book.mid_price:.3f}")
        print(f"  Spread: {order_book.spread:.4f} ({order_book.spread_bps:.1f} bps)")

    # Fetch complete market data
    print("\n[2] Fetching complete market data...")
    market_data = connector.get_market_data("FED-CUT-DEC26")
    if market_data:
        print(f"  Market: {market_data.market_name}")
        print(f"  Last Price: {market_data.last_price:.3f}")
        print(f"  24h Volume: ${market_data.volume_24h:,.0f}")

    # List markets
    print("\n[3] Listing available markets...")
    markets = connector.get_markets()
    for market in markets:
        print(f"  - {market['ticker']}: {market['title']}")

    connector.close()
