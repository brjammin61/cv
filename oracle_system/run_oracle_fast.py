#!/usr/bin/env python3
"""
The Oracle - Fast Polling Mode
High-frequency REST API polling (every 30s) as WebSocket fallback.

Author: Claude (Anthropic)
Mode: PRODUCTION FAST POLLING
"""

import asyncio
import argparse
import logging
import signal
import sys
from datetime import datetime
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.mod_06_data_collector import DataCollector
from modules.realtime_signal_generator import RealtimeSignalGenerator
from modules.mod_09_auto_executor import AutoExecutor, ExecutionMode
from modules.mod_10_ml_optimizer import MLOptimizer

# Setup logging
def setup_logging():
    """Configure logging with colors and file output."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f"logs/oracle_fast_{datetime.now().strftime('%Y%m%d')}.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

logger = logging.getLogger(__name__)


class OracleFastPolling:
    """
    Oracle with fast REST API polling (30 second intervals).
    Faster than batch mode, more reliable than WebSocket during testing.
    """

    def __init__(self, mode: str = "paper"):
        """
        Initialize Oracle in fast polling mode.

        Args:
            mode: 'paper' (simulated trades) or 'live' (real trades)
        """
        self.mode = mode
        self.running = False

        # Initialize components
        self.data_collector = DataCollector(
            db_path="data/oracle_data.db",
            collection_interval=30  # 30 seconds (vs 300s default)
        )

        self.signal_generator = RealtimeSignalGenerator()

        # Initialize Auto-Executor
        execution_mode = ExecutionMode.PAPER if mode == "paper" else ExecutionMode.LIVE

        self.auto_executor = AutoExecutor(
            mode=execution_mode,
            max_position_size_usd=50.0,  # Conservative $50 max per trade
            max_total_exposure_usd=250.0,  # Max $250 total exposure
            min_edge_to_trade=3.0,  # Minimum 3 cent edge
            min_conviction="MEDIUM",  # Allow MEDIUM+ signals
            max_trades_per_day=10,  # Max 10 trades per day
            kalshi_connector=self.data_collector.kalshi  # Pass Kalshi connector
        )

        # Initialize ML Optimizer
        self.ml_optimizer = MLOptimizer(db_path="data/oracle_data.db")

        # Statistics
        self.cycles_completed = 0
        self.signals_generated = 0
        self.trades_executed = 0
        self.start_time = None

        logger.info(f"🔮 Oracle initialized in FAST POLLING mode ({mode.upper()})")
        logger.info(f"📝 Auto-Execution: {'ENABLED (PAPER MODE)' if mode == 'paper' else 'ENABLED (LIVE MODE - REAL MONEY)'}")
        logger.info(f"🧠 ML Optimizer: ENABLED")

    async def _collection_loop(self):
        """Data collection loop (every 30 seconds)."""
        while self.running:
            try:
                # Collect data
                stats = self.data_collector.run_collection_cycle()

                self.cycles_completed += 1

                logger.info(
                    f"📊 Cycle {self.cycles_completed}: "
                    f"{stats.get('snapshots', 0)} snapshots collected"
                )

                # Generate signals for each market
                from config.markets import MarketRegistry
                registry = MarketRegistry()

                for market in registry.get_all_markets():
                    if market.kalshi_ticker:
                        # Get latest snapshot
                        snapshot = self._get_latest_snapshot(market.kalshi_ticker)

                        if snapshot:
                            # Convert to OrderBookData
                            from connectors.data_models import OrderBookData, Exchange

                            order_book = OrderBookData(
                                exchange=Exchange.KALSHI,
                                market_id=market.kalshi_ticker,
                                market_name=market.name,
                                best_bid=snapshot['best_bid'],
                                best_ask=snapshot['best_ask'],
                                bid_size=snapshot.get('bid_size', 0),
                                ask_size=snapshot.get('ask_size', 0),
                                timestamp=datetime.fromisoformat(snapshot['timestamp'])
                            )

                            # Generate signals
                            signals = self.signal_generator.process_market_update(order_book)

                            if signals:
                                self.signals_generated += len(signals)

                                for signal in signals:
                                    logger.info(
                                        f"🎯 SIGNAL: {signal.strategy} | "
                                        f"{signal.market_name} | "
                                        f"{signal.signal_type} | "
                                        f"Edge: {signal.edge_cents:.2f}¢ | "
                                        f"Conviction: {signal.conviction}"
                                    )

                                    # Convert Signal to dict for auto_executor
                                    signal_dict = {
                                        'strategy': signal.strategy,
                                        'market_name': signal.market_name,
                                        'market_ticker': signal.market_ticker,
                                        'market_id': signal.market_ticker,
                                        'signal_type': signal.signal_type,
                                        'edge_cents': signal.edge_cents,
                                        'conviction': signal.conviction,
                                        'market_price': signal.entry_price or order_book.mid_price,
                                        'rationale': f"{signal.strategy} - {signal.conviction} conviction"
                                    }

                                    # Evaluate if we should execute this signal
                                    should_execute, reason, position_size = self.auto_executor.should_execute_signal(signal_dict)

                                    if should_execute:
                                        # Execute the trade (paper or live)
                                        logger.info(f"✅ Executing: {reason}")
                                        result = self.auto_executor.execute_trade(signal_dict, position_size)

                                        if result and result.get('executed'):
                                            self.trades_executed += 1
                                            logger.info(
                                                f"💵 TRADE EXECUTED: {result['mode'].upper()} | "
                                                f"Size: ${position_size:.2f} | "
                                                f"Order: {result.get('order_id', 'N/A')}"
                                            )
                                    else:
                                        logger.debug(f"⏭️  Skipping: {reason}")

                # Wait 30 seconds
                await asyncio.sleep(30)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in collection loop: {e}", exc_info=True)
                await asyncio.sleep(30)

    def _get_latest_snapshot(self, market_ticker: str) -> dict:
        """Get latest snapshot from database."""
        import sqlite3

        conn = sqlite3.connect(self.data_collector.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT timestamp, best_bid, best_ask, mid_price, spread, bid_size, ask_size
            FROM market_snapshots
            WHERE exchange = 'kalshi' AND market_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (market_ticker,))

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

    async def _ml_optimizer_loop(self):
        """ML optimization loop (runs every 30 minutes)."""
        while self.running:
            try:
                await asyncio.sleep(1800)  # 30 minutes

                logger.info("🧠 Running ML optimization...")

                # Prepare training data from recent market snapshots
                X, y = self.ml_optimizer.prepare_training_data(days=7)

                if len(X) > 10:
                    # Train price predictor
                    self.ml_optimizer.train_price_predictor(X, y)

                # Optimize strategy parameters based on outcomes
                optimized_params = self.ml_optimizer.optimize_parameters(strategy="all")

                if optimized_params:
                    logger.info(f"✅ Optimized {len(optimized_params)} strategies")
                    for strategy, params in optimized_params.items():
                        logger.info(
                            f"  {strategy}: min_edge={params['min_edge_threshold']:.2f}¢, "
                            f"win_rate={params['expected_win_rate']:.1%}"
                        )
                else:
                    logger.info("ℹ️  Not enough trade history for optimization yet")

                logger.info("✅ ML optimization complete")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"ML optimizer error: {e}", exc_info=True)

    async def start(self):
        """Start The Oracle in fast polling mode."""
        logger.info("=" * 80)
        logger.info("🔮 THE ORACLE - FAST POLLING MODE")
        logger.info("=" * 80)
        logger.info(f"Mode: {self.mode.upper()}")
        logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("")
        logger.info("📡 Method: REST API polling")
        logger.info("⚡ Interval: 30 seconds (10x faster than batch)")
        logger.info("🎯 Signals: After each collection cycle")
        logger.info("🧠 ML: Every 30 minutes")
        logger.info("=" * 80)

        self.running = True
        self.start_time = datetime.now()

        # Start collection loop
        collection_task = asyncio.create_task(self._collection_loop())

        # Start ML optimizer loop
        ml_task = asyncio.create_task(self._ml_optimizer_loop())

        logger.info("")
        logger.info("✅ Oracle is running in fast polling mode!")
        logger.info("📊 Collecting data every 30 seconds...")
        logger.info("⏹️  Press Ctrl+C to stop")
        logger.info("")

        try:
            # Keep running until interrupted
            while self.running:
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            pass

        finally:
            # Cleanup
            collection_task.cancel()
            ml_task.cancel()

    async def stop(self):
        """Stop The Oracle."""
        logger.info("\n🛑 Stopping Oracle...")
        self.running = False

        # Final stats
        logger.info("=" * 80)
        logger.info("📊 FINAL STATISTICS")
        logger.info("=" * 80)
        logger.info(f"Collection Cycles: {self.cycles_completed}")
        logger.info(f"Signals Generated: {self.signals_generated}")
        logger.info(f"Trades Executed: {self.trades_executed}")

        # Get executor stats
        executor_stats = self.auto_executor.get_status()
        logger.info(f"Win Rate: {executor_stats['win_rate']:.1f}%")
        logger.info(f"Total P&L: ${executor_stats['total_pnl']:.2f}")

        if self.start_time:
            runtime = (datetime.now() - self.start_time).total_seconds()
            logger.info(f"Runtime: {runtime/60:.1f} minutes")

        logger.info("=" * 80)
        logger.info("👋 Oracle stopped")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="The Oracle - Fast Polling Mode")
    parser.add_argument(
        "--mode",
        choices=["paper", "live"],
        default="paper",
        help="Trading mode: paper (simulated) or live (real money)"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging()

    # Create Oracle instance
    oracle = OracleFastPolling(mode=args.mode)

    # Handle graceful shutdown
    def signal_handler(sig, frame):
        logger.info("\n⚠️  Interrupt received...")
        asyncio.create_task(oracle.stop())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start Oracle
    try:
        await oracle.start()
    except KeyboardInterrupt:
        await oracle.stop()


if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Error: Python 3.7+ required")
        sys.exit(1)

    # Run
    asyncio.run(main())
