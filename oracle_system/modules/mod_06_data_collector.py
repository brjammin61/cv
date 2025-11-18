"""
Module 6: Data Collector

Automated real-time market data collection system.
Scrapes Kalshi and Polymarket every N minutes and stores in database.

NO API KEYS REQUIRED - Uses public endpoints only.
"""

import logging
import sqlite3
import time
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

from connectors import KalshiConnector, PolymarketConnector
from connectors.data_models import OrderBookData, Exchange
from config.markets import MarketRegistry

logger = logging.getLogger(__name__)


class DataCollector:
    """
    Automated market data collection system.

    Collects real-time order book data from Kalshi and Polymarket,
    stores in SQLite database for backtesting and validation.
    """

    def __init__(
        self,
        db_path: str = "data/oracle_data.db",
        collection_interval: int = 300  # 5 minutes
    ):
        """
        Initialize the data collector.

        Args:
            db_path (str): Path to SQLite database
            collection_interval (int): Seconds between collections
        """
        self.db_path = db_path
        self.collection_interval = collection_interval

        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_database()

        # Initialize connectors with REAL API credentials
        self.kalshi = KalshiConnector(simulate_data=False)
        self.polymarket = PolymarketConnector(simulate_data=False)

        # Load market registry
        self.registry = MarketRegistry()

        logger.info(f"DataCollector initialized (interval: {collection_interval}s)")

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

        # Table: collection_runs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS collection_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at DATETIME NOT NULL,
                completed_at DATETIME,
                markets_collected INTEGER,
                errors INTEGER,
                status TEXT
            )
        """)

        # Create indices for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp
            ON market_snapshots(timestamp)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_snapshots_market
            ON market_snapshots(exchange, market_id)
        """)

        conn.commit()
        conn.close()

        logger.info(f"Database initialized: {self.db_path}")

    def collect_market_snapshot(self, market_def) -> Optional[Dict]:
        """
        Collect snapshot for a single market.

        Args:
            market_def: MarketDefinition from registry

        Returns:
            Dict with snapshot data or None if failed
        """
        snapshots = []

        # Collect from Kalshi
        if market_def.kalshi_ticker and self.kalshi.connected:
            try:
                kalshi_book = self.kalshi.get_order_book(
                    market_def.kalshi_ticker,
                    market_def.name
                )

                if kalshi_book:
                    snapshots.append({
                        'exchange': 'kalshi',
                        'market_id': market_def.kalshi_ticker,
                        'market_name': market_def.name,
                        'best_bid': kalshi_book.best_bid,
                        'best_ask': kalshi_book.best_ask,
                        'mid_price': kalshi_book.mid_price,
                        'spread': kalshi_book.spread,
                        'bid_size': kalshi_book.bid_size,
                        'ask_size': kalshi_book.ask_size,
                        'timestamp': kalshi_book.timestamp
                    })
            except Exception as e:
                logger.error(f"Failed to collect Kalshi data for {market_def.name}: {e}")

        # Collect from Polymarket
        if market_def.polymarket_condition_id and self.polymarket.connected:
            try:
                poly_book = self.polymarket.get_order_book(
                    market_def.polymarket_condition_id,
                    market_def.name
                )

                if poly_book:
                    snapshots.append({
                        'exchange': 'polymarket',
                        'market_id': market_def.polymarket_condition_id,
                        'market_name': market_def.name,
                        'best_bid': poly_book.best_bid,
                        'best_ask': poly_book.best_ask,
                        'mid_price': poly_book.mid_price,
                        'spread': poly_book.spread,
                        'bid_size': poly_book.bid_size,
                        'ask_size': poly_book.ask_size,
                        'timestamp': poly_book.timestamp
                    })
            except Exception as e:
                logger.error(f"Failed to collect Polymarket data for {market_def.name}: {e}")

        return snapshots

    def save_snapshots(self, snapshots: List[Dict]):
        """Save market snapshots to database."""
        if not snapshots:
            return

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

    def run_collection_cycle(self) -> Dict:
        """
        Run a single collection cycle across all markets.

        Returns:
            Dict with cycle statistics
        """
        logger.info("Starting collection cycle...")

        start_time = datetime.now()
        all_snapshots = []
        errors = 0

        # Start collection run in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO collection_runs (started_at, status)
            VALUES (?, ?)
        """, (start_time, 'running'))
        run_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Collect data for all active markets
        markets = self.registry.get_all_markets()

        for market in markets:
            try:
                snapshots = self.collect_market_snapshot(market)
                if snapshots:
                    all_snapshots.extend(snapshots)
            except Exception as e:
                logger.error(f"Error collecting {market.name}: {e}")
                errors += 1

        # Save all snapshots
        self.save_snapshots(all_snapshots)

        # Update collection run
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE collection_runs
            SET completed_at = ?, markets_collected = ?, errors = ?, status = ?
            WHERE id = ?
        """, (end_time, len(all_snapshots), errors, 'completed', run_id))
        conn.commit()
        conn.close()

        stats = {
            'duration': duration,
            'snapshots_collected': len(all_snapshots),
            'markets_attempted': len(markets),
            'errors': errors,
            'timestamp': end_time
        }

        logger.info(
            f"Collection cycle completed: {len(all_snapshots)} snapshots "
            f"in {duration:.1f}s (errors: {errors})"
        )

        return stats

    def run_continuous(self):
        """
        Run continuous data collection loop.

        This method runs forever, collecting data every N seconds.
        Use Ctrl+C to stop.
        """
        logger.info(f"Starting continuous collection (every {self.collection_interval}s)")
        logger.info("Press Ctrl+C to stop")

        cycle_count = 0

        try:
            while True:
                cycle_count += 1
                logger.info(f"\n{'='*60}")
                logger.info(f"Collection Cycle #{cycle_count}")
                logger.info(f"{'='*60}")

                try:
                    stats = self.run_collection_cycle()
                    logger.info(f"✅ Cycle complete: {stats['snapshots_collected']} snapshots")
                except Exception as e:
                    logger.error(f"❌ Cycle failed: {e}")

                logger.info(f"Sleeping for {self.collection_interval} seconds...")
                time.sleep(self.collection_interval)

        except KeyboardInterrupt:
            logger.info("\n\n🛑 Data collection stopped by user")
            logger.info(f"Total cycles completed: {cycle_count}")

    def get_statistics(self) -> Dict:
        """Get collection statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Total snapshots
        cursor.execute("SELECT COUNT(*) FROM market_snapshots")
        total_snapshots = cursor.fetchone()[0]

        # Snapshots by exchange
        cursor.execute("""
            SELECT exchange, COUNT(*)
            FROM market_snapshots
            GROUP BY exchange
        """)
        by_exchange = dict(cursor.fetchall())

        # Recent collection runs
        cursor.execute("""
            SELECT COUNT(*), AVG(markets_collected), SUM(errors)
            FROM collection_runs
            WHERE status = 'completed'
        """)
        runs_data = cursor.fetchone()

        # Date range
        cursor.execute("""
            SELECT MIN(timestamp), MAX(timestamp)
            FROM market_snapshots
        """)
        date_range = cursor.fetchone()

        conn.close()

        return {
            'total_snapshots': total_snapshots,
            'by_exchange': by_exchange,
            'total_runs': runs_data[0] or 0,
            'avg_markets_per_run': runs_data[1] or 0,
            'total_errors': runs_data[2] or 0,
            'earliest_data': date_range[0],
            'latest_data': date_range[1]
        }

    def export_data(self, output_file: str = "data/market_data_export.csv"):
        """Export all market data to CSV."""
        import pandas as pd

        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM market_snapshots ORDER BY timestamp", conn)
        conn.close()

        df.to_csv(output_file, index=False)
        logger.info(f"Data exported to {output_file}")

        return output_file


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/data_collector.log'),
            logging.StreamHandler()
        ]
    )

    print("=" * 80)
    print("DATA COLLECTOR - Module 6")
    print("=" * 80)

    # Initialize collector
    collector = DataCollector(
        db_path="data/oracle_data.db",
        collection_interval=300  # 5 minutes
    )

    print("\n[1] Running single collection cycle...")
    stats = collector.run_collection_cycle()
    print(f"✅ Collected {stats['snapshots_collected']} snapshots in {stats['duration']:.1f}s")

    print("\n[2] Collection statistics:")
    stats = collector.get_statistics()
    print(f"  Total snapshots: {stats['total_snapshots']}")
    print(f"  By exchange: {stats['by_exchange']}")
    print(f"  Total runs: {stats['total_runs']}")

    print("\n[3] To run continuous collection:")
    print("  collector.run_continuous()")
    print("\n⚠️  This will run forever. Use Ctrl+C to stop.")
