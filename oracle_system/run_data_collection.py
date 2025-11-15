#!/usr/bin/env python3
"""
24/7 Data Collection & Signal Tracking Script

This script runs continuously collecting market data and tracking Oracle signals.

Usage:
    python run_data_collection.py

Or run in background:
    nohup python run_data_collection.py > logs/data_collection_output.log 2>&1 &

To stop:
    Press Ctrl+C (or kill the process if running in background)
"""

import logging
import time
import signal
import sys
from datetime import datetime
from pathlib import Path

# Import Oracle modules
from modules.mod_06_data_collector import DataCollector
from modules.mod_07_signal_tracker import SignalTracker
from modules import (
    BiasCorrector,
    FavoriteLongshotAdjuster,
    RiskFreeRateAdjuster,
    DutchBookDetector,
    SpatialArbitrageDetector
)
from config.markets import MarketRegistry
from config.parameters import OracleParameters
from connectors import KalshiConnector, PolymarketConnector


# ============================================================================
# CONFIGURATION
# ============================================================================

# Data collection interval (seconds)
COLLECTION_INTERVAL = 300  # 5 minutes

# Signal generation interval (seconds)
SIGNAL_INTERVAL = 600  # 10 minutes

# Auto-update signals from market data (seconds)
SIGNAL_UPDATE_INTERVAL = 300  # 5 minutes

# Auto-close expired signals after (hours)
SIGNAL_EXPIRY_HOURS = 24

# Minimum edge to log signals (cents)
MIN_EDGE_TO_LOG = 1.0

# Minimum conviction to log signals
MIN_CONVICTION = "MEDIUM"

# Database path
DB_PATH = "data/oracle_data.db"


# ============================================================================
# SIGNAL HANDLER (For graceful shutdown)
# ============================================================================

shutdown_requested = False


def signal_handler(sig, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_requested
    print("\n\n🛑 Shutdown requested. Finishing current cycle...")
    shutdown_requested = True


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


# ============================================================================
# SETUP LOGGING
# ============================================================================

# Ensure logs directory exists
Path("logs").mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/data_collection.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


# ============================================================================
# MAIN SYSTEM
# ============================================================================

class OracleDataSystem:
    """
    Complete 24/7 data collection and signal tracking system.

    This orchestrates:
    - Data collection every N minutes
    - Signal generation every M minutes
    - Signal tracking and validation
    - Performance monitoring
    """

    def __init__(self):
        """Initialize the complete Oracle data system."""
        logger.info("=" * 80)
        logger.info("ORACLE DATA COLLECTION SYSTEM - STARTING")
        logger.info("=" * 80)

        # Initialize components
        logger.info("Initializing components...")

        self.data_collector = DataCollector(
            db_path=DB_PATH,
            collection_interval=COLLECTION_INTERVAL
        )

        self.signal_tracker = SignalTracker(db_path=DB_PATH)

        # Load configuration
        self.params = OracleParameters()
        self.registry = MarketRegistry()

        # Initialize analytical engines
        self.engines = {
            'BiasCorrector': BiasCorrector(
                shy_voter_weight=self.params.bias_corrector.shy_voter_weight
            ),
            'FLB': FavoriteLongshotAdjuster(
                favorite_threshold=self.params.flb_adjuster.favorite_threshold,
                longshot_threshold=self.params.flb_adjuster.longshot_threshold
            ),
            'RFR': RiskFreeRateAdjuster(
                risk_free_rate=self.params.rfr_adjuster.risk_free_rate
            ),
            'DutchBook': DutchBookDetector(
                transaction_fee_per_share=self.params.dutchbook.transaction_fee_per_share
            ),
            'SpatialArb': SpatialArbitrageDetector(
                total_fee_cost=self.params.spatial_arb.total_fee_cost
            )
        }

        # Initialize connectors
        # TODO: Set simulate_data=False when you have API keys
        self.kalshi = KalshiConnector(simulate_data=True)
        self.polymarket = PolymarketConnector(simulate_data=True)

        # Counters
        self.data_cycles = 0
        self.signal_cycles = 0
        self.total_signals_logged = 0

        self.last_data_collection = None
        self.last_signal_generation = None
        self.last_signal_update = None

        logger.info("✅ All components initialized")

    def collect_data_cycle(self):
        """Run a data collection cycle."""
        logger.info("\n" + "=" * 80)
        logger.info(f"DATA COLLECTION CYCLE #{self.data_cycles + 1}")
        logger.info("=" * 80)

        try:
            stats = self.data_collector.run_collection_cycle()
            self.data_cycles += 1
            self.last_data_collection = datetime.now()

            logger.info(
                f"✅ Data collection complete: {stats['snapshots_collected']} snapshots "
                f"in {stats['duration']:.1f}s"
            )

            return stats

        except Exception as e:
            logger.error(f"❌ Data collection failed: {e}", exc_info=True)
            return None

    def generate_signals_cycle(self):
        """Generate and log signals from current market data."""
        logger.info("\n" + "=" * 80)
        logger.info(f"SIGNAL GENERATION CYCLE #{self.signal_cycles + 1}")
        logger.info("=" * 80)

        signals_logged = 0

        try:
            # Get spatial arbitrage markets
            spatial_markets = self.registry.get_spatial_arb_markets()

            for market in spatial_markets:
                try:
                    # Fetch current order books
                    kalshi_book = self.kalshi.get_order_book(
                        market.kalshi_ticker or "DEMO",
                        market.name
                    )

                    poly_book = self.polymarket.get_order_book(
                        market.polymarket_condition_id or "0x...",
                        market.name
                    )

                    if kalshi_book and poly_book:
                        # Check for spatial arbitrage
                        signal, rationale = self.engines['SpatialArb'].find_arbitrage(
                            kalshi_book.best_bid,
                            kalshi_book.best_ask,
                            poly_book.best_bid,
                            poly_book.best_ask,
                            market.name
                        )

                        if signal != "HOLD":
                            # Calculate edge
                            if signal == "BUY_KALSHI_SELL_POLY":
                                edge = (poly_book.best_bid - kalshi_book.best_ask) * 100
                            else:
                                edge = (kalshi_book.best_bid - poly_book.best_ask) * 100

                            if edge >= MIN_EDGE_TO_LOG:
                                # Log signal
                                signal_id = self.signal_tracker.log_signal(
                                    strategy="SpatialArbitrage",
                                    market_name=market.name,
                                    signal_type=signal,
                                    edge_cents=edge,
                                    conviction="HIGH",
                                    market_price=kalshi_book.mid_price,
                                    rationale=rationale,
                                    exchange="kalshi",
                                    market_id=market.kalshi_ticker
                                )

                                signals_logged += 1
                                logger.info(f"  ✅ Signal #{signal_id} logged: {market.name} - {signal}")

                except Exception as e:
                    logger.error(f"  ❌ Failed to analyze {market.name}: {e}")

            self.signal_cycles += 1
            self.total_signals_logged += signals_logged
            self.last_signal_generation = datetime.now()

            logger.info(f"✅ Signal generation complete: {signals_logged} new signals")

            return signals_logged

        except Exception as e:
            logger.error(f"❌ Signal generation failed: {e}", exc_info=True)
            return 0

    def update_signals_cycle(self):
        """Update active signals with current market prices."""
        logger.info("\nUpdating active signals...")

        try:
            updated = self.signal_tracker.auto_update_signals_from_market_data()
            expired = self.signal_tracker.close_expired_signals(hours=SIGNAL_EXPIRY_HOURS)

            self.last_signal_update = datetime.now()

            logger.info(f"  ✅ Updated {updated} signals, closed {expired} expired")

            return updated

        except Exception as e:
            logger.error(f"  ❌ Signal update failed: {e}", exc_info=True)
            return 0

    def print_status(self):
        """Print system status."""
        # Get statistics
        data_stats = self.data_collector.get_statistics()
        signal_stats = self.signal_tracker.get_performance_stats(days=7)

        print("\n" + "=" * 80)
        print("SYSTEM STATUS")
        print("=" * 80)

        print(f"\n📊 Data Collection:")
        print(f"  Total Cycles: {self.data_cycles}")
        print(f"  Total Snapshots: {data_stats['total_snapshots']}")
        print(f"  Last Collection: {self.last_data_collection or 'Never'}")

        print(f"\n🎯 Signal Tracking:")
        print(f"  Total Cycles: {self.signal_cycles}")
        print(f"  Total Signals Logged: {self.total_signals_logged}")
        print(f"  Last Generation: {self.last_signal_generation or 'Never'}")

        print(f"\n📈 Performance (Last 7 days):")
        print(f"  Total Signals: {signal_stats['total_signals']}")
        print(f"  Win Rate: {signal_stats['win_rate']:.1f}%")
        print(f"  Avg Edge: {signal_stats['avg_edge']:+.2f}¢")

        print("\n" + "=" * 80)

    def run(self):
        """Run the complete system in a continuous loop."""
        logger.info("\n🚀 Starting 24/7 data collection system")
        logger.info(f"Data collection interval: {COLLECTION_INTERVAL}s ({COLLECTION_INTERVAL/60:.1f} min)")
        logger.info(f"Signal generation interval: {SIGNAL_INTERVAL}s ({SIGNAL_INTERVAL/60:.1f} min)")
        logger.info("Press Ctrl+C to stop gracefully\n")

        # Initial collection
        self.collect_data_cycle()
        self.generate_signals_cycle()
        self.print_status()

        last_data_time = time.time()
        last_signal_time = time.time()
        last_update_time = time.time()

        # Main loop
        while not shutdown_requested:
            try:
                current_time = time.time()

                # Check if it's time for data collection
                if current_time - last_data_time >= COLLECTION_INTERVAL:
                    self.collect_data_cycle()
                    last_data_time = current_time

                # Check if it's time for signal generation
                if current_time - last_signal_time >= SIGNAL_INTERVAL:
                    self.generate_signals_cycle()
                    last_signal_time = current_time

                # Check if it's time to update signals
                if current_time - last_update_time >= SIGNAL_UPDATE_INTERVAL:
                    self.update_signals_cycle()
                    last_update_time = current_time

                    # Print status every hour
                    if self.data_cycles % 12 == 0:  # Every ~hour if 5min intervals
                        self.print_status()

                # Sleep for 30 seconds before checking again
                time.sleep(30)

            except Exception as e:
                logger.error(f"❌ Error in main loop: {e}", exc_info=True)
                time.sleep(60)  # Wait a minute before retrying

        # Shutdown
        logger.info("\n" + "=" * 80)
        logger.info("SHUTTING DOWN")
        logger.info("=" * 80)

        self.print_status()

        logger.info("\n✅ Oracle Data Collection System stopped gracefully")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("THE ORACLE - 24/7 Data Collection & Signal Tracking")
    print("=" * 80)
    print("\nThis script will:")
    print("  1. Collect market data every 5 minutes")
    print("  2. Generate signals every 10 minutes")
    print("  3. Track signal performance automatically")
    print("  4. Build a historical database for backtesting")
    print("\n⚠️  Currently running in SIMULATION mode")
    print("   (Configure API keys in config/api_keys.py for live data)")
    print("\n" + "=" * 80)

    try:
        # Create and run system
        system = OracleDataSystem()
        system.run()

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
