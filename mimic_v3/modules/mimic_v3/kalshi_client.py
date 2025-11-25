"""
KalshiClient.py - Async REST & WebSocket Client for Kalshi API
MIMIC V3.1 - Production Ready

Handles:
- Authentication (API Key + Secret)
- REST endpoints (markets, events, orders)
- WebSocket streaming (orderbook, trades, settlements)
- Rate limiting & circuit breaker
- Automatic reconnection
"""

import os
import asyncio
import aiohttp
import hashlib
import hmac
import time
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum


class OrderSide(Enum):
    YES = "yes"
    NO = "no"


class OrderType(Enum):
    LIMIT = "limit"
    MARKET = "market"


@dataclass
class RateLimiter:
    """Token bucket rate limiter"""
    requests_per_second: float = 10.0
    tokens: float = field(default=10.0)
    last_update: float = field(default_factory=time.time)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def acquire(self):
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(self.requests_per_second, self.tokens + elapsed * self.requests_per_second)
            self.last_update = now

            if self.tokens < 1:
                wait_time = (1 - self.tokens) / self.requests_per_second
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1


@dataclass
class CircuitBreaker:
    """Circuit breaker for fault tolerance"""
    failure_threshold: int = 5
    reset_timeout: float = 60.0
    failures: int = 0
    last_failure: float = 0
    state: str = "closed"  # closed, open, half-open

    def record_failure(self):
        self.failures += 1
        self.last_failure = time.time()
        if self.failures >= self.failure_threshold:
            self.state = "open"
            logging.warning(f"Circuit breaker OPENED after {self.failures} failures")

    def record_success(self):
        self.failures = 0
        self.state = "closed"

    def can_execute(self) -> bool:
        if self.state == "closed":
            return True
        if self.state == "open":
            if time.time() - self.last_failure > self.reset_timeout:
                self.state = "half-open"
                return True
            return False
        return True  # half-open allows one request


class KalshiClient:
    """
    Production-grade Kalshi API client with:
    - HMAC authentication
    - Rate limiting
    - Circuit breaker
    - WebSocket streaming
    - Automatic reconnection
    """

    # API Endpoints
    API_BASE = "https://api.elections.kalshi.com/trade-api/v2"
    WS_BASE = "wss://api.elections.kalshi.com/trade-api/ws/v2"

    # Demo endpoints for testing
    DEMO_API_BASE = "https://demo-api.kalshi.co/trade-api/v2"
    DEMO_WS_BASE = "wss://demo-api.kalshi.co/trade-api/ws/v2"

    def __init__(
        self,
        api_key: str = None,
        api_secret: str = None,
        demo_mode: bool = False,
        logger: logging.Logger = None
    ):
        self.api_key = api_key or os.getenv("KALSHI_API_KEY")
        self.api_secret = api_secret or os.getenv("KALSHI_API_SECRET")
        self.demo_mode = demo_mode

        self.base_url = self.DEMO_API_BASE if demo_mode else self.API_BASE
        self.ws_url = self.DEMO_WS_BASE if demo_mode else self.WS_BASE

        self.logger = logger or logging.getLogger(__name__)
        self.rate_limiter = RateLimiter()
        self.circuit_breaker = CircuitBreaker()

        self._session: Optional[aiohttp.ClientSession] = None
        self._ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._ws_handlers: Dict[str, List[Callable]] = {}
        self._ws_running = False
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 10

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def connect(self):
        """Initialize HTTP session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self

    async def close(self):
        """Clean shutdown"""
        self._ws_running = False
        if self._ws and not self._ws.closed:
            await self._ws.close()
        if self._session and not self._session.closed:
            await self._session.close()

    def _generate_signature(self, timestamp: str, method: str, path: str, body: str = "") -> str:
        """
        Generate HMAC-SHA256 signature for Kalshi API authentication.
        """
        message = f"{timestamp}{method}{path}{body}"
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    def _get_auth_headers(self, method: str, path: str, body: str = "") -> Dict[str, str]:
        """Generate authenticated headers for API requests"""
        timestamp = str(int(time.time() * 1000))
        signature = self._generate_signature(timestamp, method, path, body)

        return {
            "KALSHI-ACCESS-KEY": self.api_key,
            "KALSHI-ACCESS-SIGNATURE": signature,
            "KALSHI-ACCESS-TIMESTAMP": timestamp,
            "Content-Type": "application/json"
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Dict = None,
        params: Dict = None,
        auth_required: bool = True
    ) -> Dict:
        """
        Make authenticated API request with rate limiting and circuit breaker.
        """
        if not self.circuit_breaker.can_execute():
            raise Exception("Circuit breaker is open - too many failures")

        await self.rate_limiter.acquire()

        path = f"/trade-api/v2{endpoint}"
        url = f"{self.base_url}{endpoint}"

        body = json.dumps(data) if data else ""
        headers = self._get_auth_headers(method, path, body) if auth_required else {}

        try:
            async with self._session.request(
                method,
                url,
                headers=headers,
                json=data,
                params=params
            ) as response:
                if response.status == 429:  # Rate limited
                    retry_after = int(response.headers.get("Retry-After", 5))
                    self.logger.warning(f"Rate limited, waiting {retry_after}s")
                    await asyncio.sleep(retry_after)
                    return await self._request(method, endpoint, data, params, auth_required)

                if response.status >= 400:
                    error_text = await response.text()
                    self.circuit_breaker.record_failure()
                    raise Exception(f"API Error {response.status}: {error_text}")

                self.circuit_breaker.record_success()
                return await response.json()

        except aiohttp.ClientError as e:
            self.circuit_breaker.record_failure()
            raise Exception(f"Connection error: {e}")

    # ==================== REST API METHODS ====================

    async def get_exchange_status(self) -> Dict:
        """Get exchange operational status"""
        return await self._request("GET", "/exchange/status", auth_required=False)

    async def get_markets(
        self,
        event_ticker: str = None,
        status: str = "open",
        limit: int = 100,
        cursor: str = None
    ) -> Dict:
        """
        Get list of markets with optional filters.

        Args:
            event_ticker: Filter by event
            status: open, closed, settled
            limit: Max results (up to 1000)
            cursor: Pagination cursor
        """
        params = {"status": status, "limit": limit}
        if event_ticker:
            params["event_ticker"] = event_ticker
        if cursor:
            params["cursor"] = cursor

        return await self._request("GET", "/markets", params=params)

    async def get_market(self, ticker: str) -> Dict:
        """Get detailed market info by ticker"""
        return await self._request("GET", f"/markets/{ticker}")

    async def get_event(self, event_ticker: str) -> Dict:
        """Get event details including settlement rules"""
        return await self._request("GET", f"/events/{event_ticker}")

    async def get_orderbook(self, ticker: str, depth: int = 10) -> Dict:
        """Get orderbook for a market"""
        return await self._request("GET", f"/markets/{ticker}/orderbook", params={"depth": depth})

    async def get_trades(self, ticker: str, limit: int = 100, cursor: str = None) -> Dict:
        """Get recent trades for a market"""
        params = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        return await self._request("GET", f"/markets/{ticker}/trades", params=params)

    async def get_balance(self) -> Dict:
        """Get account balance"""
        return await self._request("GET", "/portfolio/balance")

    async def get_positions(self, status: str = "open") -> Dict:
        """Get current positions"""
        return await self._request("GET", "/portfolio/positions", params={"status": status})

    async def create_order(
        self,
        ticker: str,
        side: OrderSide,
        order_type: OrderType,
        count: int,
        price: int = None,  # In cents (1-99)
        client_order_id: str = None
    ) -> Dict:
        """
        Submit an order.

        Args:
            ticker: Market ticker
            side: OrderSide.YES or OrderSide.NO
            order_type: OrderType.LIMIT or OrderType.MARKET
            count: Number of contracts
            price: Limit price in cents (1-99), required for limit orders
            client_order_id: Optional client-side order ID
        """
        data = {
            "ticker": ticker,
            "side": side.value,
            "type": order_type.value,
            "count": count,
            "action": "buy"
        }

        if order_type == OrderType.LIMIT:
            if price is None:
                raise ValueError("Limit orders require a price")
            data["yes_price"] = price if side == OrderSide.YES else None
            data["no_price"] = price if side == OrderSide.NO else None

        if client_order_id:
            data["client_order_id"] = client_order_id

        return await self._request("POST", "/portfolio/orders", data=data)

    async def cancel_order(self, order_id: str) -> Dict:
        """Cancel an open order"""
        return await self._request("DELETE", f"/portfolio/orders/{order_id}")

    async def get_fills(self, ticker: str = None, limit: int = 100) -> Dict:
        """Get order fills/executions"""
        params = {"limit": limit}
        if ticker:
            params["ticker"] = ticker
        return await self._request("GET", "/portfolio/fills", params=params)

    # ==================== WEBSOCKET METHODS ====================

    def on_message(self, msg_type: str):
        """Decorator to register WebSocket message handlers"""
        def decorator(func: Callable):
            if msg_type not in self._ws_handlers:
                self._ws_handlers[msg_type] = []
            self._ws_handlers[msg_type].append(func)
            return func
        return decorator

    async def subscribe(self, channels: List[str], tickers: List[str] = None):
        """
        Subscribe to WebSocket channels.

        Channels:
        - orderbook_delta: Orderbook updates
        - ticker: Price/volume updates
        - trade: Trade executions
        - fill: Your order fills
        - order: Your order status changes
        """
        if not self._ws or self._ws.closed:
            await self._connect_websocket()

        subscribe_msg = {
            "id": int(time.time() * 1000),
            "cmd": "subscribe",
            "params": {
                "channels": channels
            }
        }

        if tickers:
            subscribe_msg["params"]["market_tickers"] = tickers

        await self._ws.send_json(subscribe_msg)
        self.logger.info(f"Subscribed to channels: {channels}")

    async def _connect_websocket(self):
        """Establish WebSocket connection with authentication"""
        timestamp = str(int(time.time() * 1000))
        path = "/trade-api/ws/v2"
        signature = self._generate_signature(timestamp, "GET", path)

        headers = {
            "KALSHI-ACCESS-KEY": self.api_key,
            "KALSHI-ACCESS-SIGNATURE": signature,
            "KALSHI-ACCESS-TIMESTAMP": timestamp
        }

        self._ws = await self._session.ws_connect(
            self.ws_url,
            headers=headers,
            heartbeat=30
        )
        self._reconnect_attempts = 0
        self.logger.info("WebSocket connected")

    async def start_websocket(self):
        """Start WebSocket message processing loop"""
        self._ws_running = True

        while self._ws_running:
            try:
                if not self._ws or self._ws.closed:
                    await self._connect_websocket()

                async for msg in self._ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        await self._handle_ws_message(json.loads(msg.data))
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        self.logger.error(f"WebSocket error: {self._ws.exception()}")
                        break
                    elif msg.type == aiohttp.WSMsgType.CLOSED:
                        self.logger.warning("WebSocket closed")
                        break

            except Exception as e:
                self.logger.error(f"WebSocket error: {e}")

            # Reconnection logic
            if self._ws_running:
                self._reconnect_attempts += 1
                if self._reconnect_attempts > self._max_reconnect_attempts:
                    self.logger.error("Max reconnection attempts reached")
                    break

                wait_time = min(2 ** self._reconnect_attempts, 60)
                self.logger.info(f"Reconnecting in {wait_time}s (attempt {self._reconnect_attempts})")
                await asyncio.sleep(wait_time)

    async def _handle_ws_message(self, data: Dict):
        """Route WebSocket messages to registered handlers"""
        msg_type = data.get("type", "unknown")

        # Handle subscribed data
        if msg_type == "subscribed":
            self.logger.debug(f"Subscription confirmed: {data}")
            return

        # Handle channel messages
        channel = data.get("channel")
        if channel and channel in self._ws_handlers:
            for handler in self._ws_handlers[channel]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(data)
                    else:
                        handler(data)
                except Exception as e:
                    self.logger.error(f"Handler error for {channel}: {e}")

        # Generic message handler
        if "message" in self._ws_handlers:
            for handler in self._ws_handlers["message"]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(data)
                    else:
                        handler(data)
                except Exception as e:
                    self.logger.error(f"Generic handler error: {e}")


# ==================== USAGE EXAMPLE ====================

async def example_usage():
    """Example showing how to use the KalshiClient"""

    async with KalshiClient(demo_mode=True) as client:
        # REST API examples
        status = await client.get_exchange_status()
        print(f"Exchange status: {status}")

        markets = await client.get_markets(status="open", limit=5)
        print(f"Found {len(markets.get('markets', []))} markets")

        # WebSocket example
        @client.on_message("trade")
        async def handle_trade(data):
            print(f"Trade: {data}")

        @client.on_message("orderbook_delta")
        async def handle_orderbook(data):
            print(f"Orderbook update: {data}")

        # Subscribe and listen
        await client.subscribe(["trade", "orderbook_delta"], tickers=["KXCPI-25DEC-T0.3"])
        await client.start_websocket()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(example_usage())
