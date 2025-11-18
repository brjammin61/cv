"""
Realtime Data Collector
Event-driven data collection using WebSocket streaming for sub-second market updates.
"""

import logging
import sqlite3
import asyncio
from datetime import datetime
from typing import Dict, Optional, Callable
from pathlib import Path
from queue import Queue
import threading

from connectors import KalshiConnector, PolymarketConnector
from connectors.data_models import OrderBookData
from config.markets import MarketRegistry

logger = logging.getLogger(__name__)


class RealtimeDataCollector:
    """
    Real-time market data collector using WebSocket streaming.

    Subscribes to market updates via WebSockets and triggers callbacks
    on every price change for event-driven signal generation.
    """

    def __init__(
        self,
        db_path: str = "data/oracle_data.db",
        on_update_callback: Optional[Callable] = None
    ):
        """
        Initialize realtime data collector.

        Args:
            db_path: Path to SQLite database
            on_update_callback: Function called on each market update
        """
        self.db_path = db_path
        self.on_update_callback = on_update_callback

        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_database()

        # Initialize connectors with real API
        self.kalshi = KalshiConnector(simulate_data=False)
        self.polymarket = PolymarketConnector(simulate_data=False)

        # Load market registry
        self.registry = MarketRegistry()

        # Event loop for async operations
        self.loop = None
        self.running = False

        # Market update queue for batch processing
        self.update_queue = Queue()

        logger.info("RealtimeDataCollector initialized (WebSocket mode)")

    def _init_database(self):
        """Initialize SQLite database with schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Table: market_snapshots
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                exchange TEXT NOT NULL,
                market_id TEXT NOT NULL,
                market_name TEXT,
                best_bid REAL NOT NULL,
                best_ask REAL NOT NULL,
                mid_price REAL NOT NULL,
                spread REAL NOT NULL,
                bid_size REAL,
                ask_size REAL,
                volume_24h REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Table: signals (for event-driven signal generation)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                strategy TEXT NOT NULL,
                market_name TEXT NOT NULL,
                market_ticker TEXT NOT NULL,
                signal_type TEXT NOT NULL,
                edge_cents REAL NOT NULL,
                conviction TEXT NOT NULL,
                entry_price REAL,
                current_price REAL,
                profit_loss REAL,
                status TEXT DEFAULT 'active',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                closed_at DATETIME
            )
        """)

        # Create indices
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp
            ON market_snapshots(timestamp)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_snapshots_market
            ON market_snapshots(exchange, market_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_signals_status
            ON signals(status)
        """)

        conn.commit()
        conn.close()

        logger.info(f"Database initialized: {self.db_path}")

    async def _market_update_handler(self, order_book: OrderBookData):
        """
        Handle incoming market update from WebSocket.

        Args:
            order_book: OrderBookData from WebSocket
        """
        try:
            # Save to database
            snapshot = {
                'timestamp': order_book.timestamp,
                'exchange': order_book.exchange.value,
                'market_id': order_book.market_id,
                'market_name': order_book.market_name,
                'best_bid': order_book.best_bid,
                'best_ask': order_book.best_ask,
                'mid_price': order_book.mid_price,
                'spread': order_book.spread,
                'bid_size': order_book.bid_size,
                'ask_size': order_book.ask_size
            }

            # Queue for batch insert (better performance)
            self.update_queue.put(snapshot)

            # Trigger callback for signal generation
            if self.on_update_callback:
                if asyncio.iscoroutinefunction(self.on_update_callback):
                    await self.on_update_callback(order_book)
                else:
                    # Run sync callback in thread pool
                    await self.loop.run_in_executor(None, self.on_update_callback, order_book)

            logger.debug(f"📊 {order_book.market_id}: ${order_book.mid_price:.2f} "
                        f"(spread: {order_book.spread:.4f})")

        except Exception as e:
            logger.error(f"Error handling market update: {e}")

    def _db_writer_thread(self):
        """Background thread for batch database writes."""
        while self.running:
            try:
                snapshots = []

                # Collect updates for up to 1 second
                import time
                deadline = time.time() + 1.0

                while time.time() < deadline and not self.update_queue.empty():
                    snapshots.append(self.update_queue.get_nowait())

                # Batch insert
                if snapshots:
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()

                    for snapshot in snapshots:
                        cursor.execute("""
                            INSERT INTO market_snapshots (
                                timestamp, exchange, market_id, market_name,
                                best_bid, best_ask, mid_price, spread,
                                bid_size, ask_size
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            snapshot['timestamp'],
                            snapshot['exchange'],
                            snapshot['market_id'],
                            snapshot['market_name'],
                            snapshot['best_bid'],
                            snapshot['best_ask'],
                            snapshot['mid_price'],
                            snapshot['spread'],
                            snapshot.get('bid_size'),
                            snapshot.get('ask_size')
                        ))

                    conn.commit()
                    conn.close()

                    logger.debug(f"💾 Saved {len(snapshots)} market updates to database")

                time.sleep(0.1)  # Small sleep to prevent CPU spinning

            except Exception as e:
                logger.error(f"DB writer error: {e}")

    async def start(self):
        """Start real-time data collection."""
        logger.info("🚀 Starting realtime data collection...")

        self.running = True
        self.loop = asyncio.get_event_loop()

        # Start background DB writer thread
        db_thread = threading.Thread(target=self._db_writer_thread, daemon=True)
        db_thread.start()

        # Connect to WebSocket
        await self.kalshi.connect_websocket()

        # Subscribe to all markets
        markets = self.registry.get_all_markets()

        for market in markets:
            if market.kalshi_ticker:
                await self.kalshi.subscribe_market(
                    market.kalshi_ticker,
                    self._market_update_handler
                )
                logger.info(f"📡 Subscribed to {market.name} ({market.kalshi_ticker})")

        logger.info(f"✅ Realtime collection started for {len(markets)} markets")
        logger.info("📊 Updates will be processed as they arrive (sub-second latency)")

    async def stop(self):
        """Stop real-time data collection."""
        logger.info("Stopping realtime data collection...")

        self.running = False

        # Unsubscribe from all markets
        markets = self.registry.get_all_markets()

        for market in markets:
            if market.kalshi_ticker:
                await self.kalshi.unsubscribe_market(market.kalshi_ticker)

        # Close connectors
        self.kalshi.close()
        self.polymarket.close()

        logger.info("Realtime data collection stopped")

    def get_latest_snapshot(self, market_id: str, exchange: str = 'kalshi') -> Optional[Dict]:
        """
        Get most recent snapshot for a market.

        Args:
            market_id: Market ticker/ID
            exchange: Exchange name

        Returns:
            Dict with snapshot data or None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT timestamp, best_bid, best_ask, mid_price, spread, bid_size, ask_size
            FROM market_snapshots
            WHERE exchange = ? AND market_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (exchange, market_id))

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'timestamp': row[0],
                'best_bid': row[1],
                'best_ask': row[2],
                'mid_price': row[3],
                'spread': row[4],
                'bid_size': row[5],
                'ask_size': row[6]
            }

        return None

    def get_price_history(self, market_id: str, exchange: str = 'kalshi',
                         minutes: int = 60) -> list:
        """
        Get price history for a market.

        Args:
            market_id: Market ticker/ID
            exchange: Exchange name
            minutes: How many minutes of history

        Returns:
            List of price snapshots
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT timestamp, mid_price, spread, bid_size, ask_size
            FROM market_snapshots
            WHERE exchange = ? AND market_id = ?
            AND timestamp > datetime('now', '-' || ? || ' minutes')
            ORDER BY timestamp ASC
        """, (exchange, market_id, minutes))

        rows = cursor.fetchall()
        conn.close()

        return [{
            'timestamp': row[0],
            'mid_price': row[1],
            'spread': row[2],
            'bid_size': row[3],
            'ask_size': row[4]
        } for row in rows]


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    async def on_market_update(order_book: OrderBookData):
        """Example callback for market updates."""
        print(f"📊 {order_book.market_name}: ${order_book.mid_price:.2f}")

    async def main():
        collector = RealtimeDataCollector(on_update_callback=on_market_update)

        try:
            await collector.start()

            # Run forever (or until Ctrl+C)
            while True:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            await collector.stop()

    asyncio.run(main())
