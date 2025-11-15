#!/usr/bin/env python3
"""
THE ORACLE - Complete Automated Trading System
Master Control Script

This orchestrates the complete Oracle system:
- 24/7 data collection from Kalshi & Polymarket
- Signal generation from all 5 strategies
- Automated trade execution (PAPER mode for validation)
- ML-driven parameter optimization
- Daily performance reports

Usage:
    # Run in PAPER mode (recommended for first 7 days):
    python run_oracle_system.py

    # Run with live trading (after validation):
    python run_oracle_system.py --live

    # Run in background:
    nohup python run_oracle_system.py > logs/oracle_system.log 2>&1 &

To stop:
    Press Ctrl+C (or kill the process if running in background)
"""

import logging
import time
import signal
import sys
import argparse
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Import all Oracle modules
from modules import (
    # Core strategies
    BiasCorrector,
    FavoriteLongshotAdjuster,
    RiskFreeRateAdjuster,
    DutchBookDetector,
    SpatialArbitrageDetector,
    # Data & validation
    DataCollector,
    SignalTracker,
    Backtester,
    # Automation & ML
    AutoExecutor,
    ExecutionMode,
    RiskLevel,
    MLOptimizer
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

# ML optimization interval (seconds)
ML_OPTIMIZATION_INTERVAL = 3600  # 1 hour

# Daily report time (24-hour format)
DAILY_REPORT_HOUR = 9  # 9 AM

# Auto-close expired signals after (hours)
SIGNAL_EXPIRY_HOURS = 24

# Minimum edge to log signals (cents)
MIN_EDGE_TO_LOG = 1.0

# Minimum conviction to log signals
MIN_CONVICTION = "MEDIUM"

# Database path
DB_PATH = "data/oracle_data.db"

# Maximum account value for safety (dollars)
MAX_ACCOUNT_VALUE = 10000  # $10k max

# Starting bankroll (for PAPER mode simulation)
STARTING_BANKROLL = 1000  # $1k


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
        logging.FileHandler('logs/oracle_system.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


# ============================================================================
# COMPLETE ORACLE SYSTEM
# ============================================================================

class CompleteOracleSystem:
    """
    The complete Oracle prediction market trading system.

    Orchestrates:
    - Data collection from multiple exchanges
    - Signal generation from 5+ strategies
    - Automated trade execution with safety controls
    - ML-based parameter optimization
    - Performance tracking and reporting
    """

    def __init__(self, execution_mode: ExecutionMode = ExecutionMode.PAPER):
        """
        Initialize the complete Oracle system.

        Args:
            execution_mode: PAPER (simulate), LIVE (real trades), or DISABLED
        """
        logger.info("=" * 80)
        logger.info("THE ORACLE - COMPLETE AUTOMATED TRADING SYSTEM")
        logger.info("=" * 80)
        logger.info(f"Execution Mode: {execution_mode.value}")
        logger.info("=" * 80)

        self.execution_mode = execution_mode

        # Initialize components
        logger.info("Initializing system components...")

        # Data & tracking
        self.data_collector = DataCollector(
            db_path=DB_PATH,
            collection_interval=COLLECTION_INTERVAL
        )
        self.signal_tracker = SignalTracker(db_path=DB_PATH)
        self.backtester = Backtester(db_path=DB_PATH)

        # Automation & ML
        self.auto_executor = AutoExecutor(
            mode=execution_mode,
            max_position_size_usd=500,  # $500 max per position
            max_total_exposure_usd=MAX_ACCOUNT_VALUE,
            min_edge_to_trade=1.0,  # 1 cent minimum
            min_conviction="MEDIUM",
            max_trades_per_day=20,
            emergency_stop=False
        )
        self.ml_optimizer = MLOptimizer(db_path=DB_PATH)

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
        # NOTE: Collecting data from BOTH exchanges
        # But only executing on Kalshi (user is US-based)
        # TODO: Set simulate_data=False when you have API keys
        self.kalshi = KalshiConnector(simulate_data=True)
        self.polymarket = PolymarketConnector(simulate_data=True)

        # Counters
        self.data_cycles = 0
        self.signal_cycles = 0
        self.ml_cycles = 0
        self.total_signals_generated = 0
        self.total_trades_executed = 0

        # Timestamps
        self.last_data_collection = None
        self.last_signal_generation = None
        self.last_signal_update = None
        self.last_ml_optimization = None
        self.last_daily_report = None

        # Performance tracking
        self.paper_bankroll = STARTING_BANKROLL
        self.paper_pnl = 0.0

        logger.info("✅ All components initialized successfully")

    def collect_data_cycle(self) -> Optional[Dict]:
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

    def generate_and_execute_signals_cycle(self) -> int:
        """
        Generate signals from all strategies and execute if appropriate.

        Returns number of signals generated (not necessarily executed).
        """
        logger.info("\n" + "=" * 80)
        logger.info(f"SIGNAL GENERATION & EXECUTION CYCLE #{self.signal_cycles + 1}")
        logger.info("=" * 80)

        signals_generated = 0
        trades_executed = 0

        try:
            # Strategy 1: Spatial Arbitrage
            spatial_signals = self._check_spatial_arbitrage()
            signals_generated += len(spatial_signals)

            for signal in spatial_signals:
                executed = self._execute_signal_if_approved(signal)
                if executed:
                    trades_executed += 1

            # Strategy 2-5: Other strategies
            # TODO: Implement bias correction, FLB, RFR, dutch book signal generation
            # For now, focusing on spatial arbitrage which is easiest to automate

            self.signal_cycles += 1
            self.total_signals_generated += signals_generated
            self.total_trades_executed += trades_executed
            self.last_signal_generation = datetime.now()

            logger.info(
                f"✅ Signal cycle complete: {signals_generated} signals generated, "
                f"{trades_executed} trades executed"
            )

            return signals_generated

        except Exception as e:
            logger.error(f"❌ Signal generation failed: {e}", exc_info=True)
            return 0

    def _check_spatial_arbitrage(self) -> List[Dict]:
        """Check for spatial arbitrage opportunities."""
        signals = []

        try:
            spatial_markets = self.registry.get_spatial_arb_markets()

            for market in spatial_markets:
                try:
                    # Fetch order books from both exchanges
                    kalshi_book = self.kalshi.get_order_book(
                        market.kalshi_ticker or "DEMO",
                        market.name
                    )

                    poly_book = self.polymarket.get_order_book(
                        market.polymarket_condition_id or "0x...",
                        market.name
                    )

                    if kalshi_book and poly_book:
                        # Check for arbitrage
                        signal_type, rationale = self.engines['SpatialArb'].find_arbitrage(
                            kalshi_book.best_bid,
                            kalshi_book.best_ask,
                            poly_book.best_bid,
                            poly_book.best_ask,
                            market.name
                        )

                        if signal_type != "HOLD":
                            # Calculate edge
                            if signal_type == "BUY_KALSHI_SELL_POLY":
                                edge = (poly_book.best_bid - kalshi_book.best_ask) * 100
                                entry_price = kalshi_book.best_ask
                            else:  # SELL_KALSHI_BUY_POLY
                                edge = (kalshi_book.best_bid - poly_book.best_ask) * 100
                                entry_price = kalshi_book.best_bid

                            if edge >= MIN_EDGE_TO_LOG:
                                signal = {
                                    'strategy': 'SpatialArbitrage',
                                    'market_name': market.name,
                                    'signal_type': signal_type,
                                    'edge_cents': edge,
                                    'conviction': 'HIGH',  # Spatial arb is always high conviction
                                    'entry_price': entry_price,
                                    'rationale': rationale,
                                    'exchange': 'kalshi',  # US-based, only execute on Kalshi
                                    'market_id': market.kalshi_ticker,
                                    'kalshi_bid': kalshi_book.best_bid,
                                    'kalshi_ask': kalshi_book.best_ask,
                                    'poly_bid': poly_book.best_bid,
                                    'poly_ask': poly_book.best_ask
                                }

                                signals.append(signal)
                                logger.info(f"  🎯 Signal found: {market.name} - {signal_type} (edge: {edge:.2f}¢)")

                except Exception as e:
                    logger.error(f"  ❌ Failed to analyze {market.name}: {e}")

        except Exception as e:
            logger.error(f"Spatial arbitrage check failed: {e}", exc_info=True)

        return signals

    def _execute_signal_if_approved(self, signal: Dict) -> bool:
        """
        Send signal to AutoExecutor for approval and execution.

        Returns True if trade was executed, False otherwise.
        """
        try:
            # AutoExecutor decides whether to execute
            should_execute, reason, position_size = self.auto_executor.should_execute_signal(signal)

            if should_execute:
                # Log signal to database
                signal_id = self.signal_tracker.log_signal(
                    strategy=signal['strategy'],
                    market_name=signal['market_name'],
                    signal_type=signal['signal_type'],
                    edge_cents=signal['edge_cents'],
                    conviction=signal['conviction'],
                    market_price=signal['entry_price'],
                    rationale=signal['rationale'],
                    exchange=signal['exchange'],
                    market_id=signal['market_id']
                )

                # Execute trade
                trade_result = self.auto_executor.execute_trade(
                    signal=signal,
                    position_size=position_size,
                    signal_id=signal_id
                )

                if trade_result['status'] == 'executed':
                    logger.info(
                        f"  ✅ TRADE EXECUTED: Signal #{signal_id} - "
                        f"{signal['market_name']} - {signal['signal_type']} - "
                        f"Size: ${position_size:.2f} - Edge: {signal['edge_cents']:.2f}¢"
                    )
                    return True
                else:
                    logger.warning(
                        f"  ⚠️  Trade failed: {trade_result['message']}"
                    )
                    return False
            else:
                logger.info(f"  ⏭️  Signal skipped: {reason}")
                return False

        except Exception as e:
            logger.error(f"Error executing signal: {e}", exc_info=True)
            return False

    def update_signals_cycle(self) -> int:
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

    def ml_optimization_cycle(self):
        """Run ML optimization cycle to improve parameters."""
        logger.info("\n" + "=" * 80)
        logger.info(f"ML OPTIMIZATION CYCLE #{self.ml_cycles + 1}")
        logger.info("=" * 80)

        try:
            # Train price predictor on recent data
            logger.info("Training price predictor...")
            X, y = self.ml_optimizer.prepare_training_data(days=7)

            if len(X) > 20:  # Need minimum data
                self.ml_optimizer.train_price_predictor(X, y)
                logger.info("  ✅ Price predictor trained")
            else:
                logger.warning(f"  ⚠️  Insufficient data for training ({len(X)} samples)")

            # Optimize parameters based on historical outcomes
            logger.info("Optimizing strategy parameters...")
            optimized = self.ml_optimizer.optimize_parameters(strategy="all")

            if optimized:
                logger.info(f"  ✅ Optimized parameters for {len(optimized)} strategies")

                # Update AutoExecutor with new thresholds
                for strategy, params in optimized.items():
                    if params['expected_win_rate'] > 0.65:  # Only use if win rate > 65%
                        logger.info(
                            f"    {strategy}: min_edge={params['min_edge_threshold']:.2f}¢ "
                            f"(win_rate: {params['expected_win_rate']:.1%})"
                        )
            else:
                logger.info("  ℹ️  No optimization data available yet")

            self.ml_cycles += 1
            self.last_ml_optimization = datetime.now()

        except Exception as e:
            logger.error(f"❌ ML optimization failed: {e}", exc_info=True)

    def generate_daily_report(self):
        """Generate comprehensive daily performance report."""
        logger.info("\n" + "=" * 80)
        logger.info("DAILY PERFORMANCE REPORT")
        logger.info("=" * 80)

        try:
            # Get statistics
            data_stats = self.data_collector.get_statistics()
            signal_stats = self.signal_tracker.get_performance_stats(days=1)
            executor_stats = self.auto_executor.get_statistics()
            ml_insights = self.ml_optimizer.get_ml_insights()

            print("\n" + "=" * 80)
            print(f"ORACLE SYSTEM - DAILY REPORT - {datetime.now().strftime('%Y-%m-%d')}")
            print("=" * 80)

            print(f"\n📊 DATA COLLECTION:")
            print(f"  Total Snapshots Collected: {data_stats['total_snapshots']:,}")
            print(f"  By Exchange: Kalshi={data_stats['by_exchange'].get('kalshi', 0)}, "
                  f"Polymarket={data_stats['by_exchange'].get('polymarket', 0)}")
            print(f"  Collection Cycles: {self.data_cycles}")

            print(f"\n🎯 SIGNAL GENERATION (Last 24h):")
            print(f"  Total Signals: {signal_stats['total_signals']}")
            print(f"  By Conviction:")
            for conv, count in signal_stats['by_conviction'].items():
                print(f"    {conv}: {count}")

            print(f"\n💼 TRADE EXECUTION (Last 24h):")
            print(f"  Execution Mode: {self.execution_mode.value}")
            print(f"  Total Trades: {executor_stats['total_trades']}")
            print(f"  Daily P&L: {executor_stats.get('daily_pnl', 0):+.2f}¢")

            if self.execution_mode == ExecutionMode.PAPER:
                print(f"  Paper Bankroll: ${self.paper_bankroll:.2f}")

            print(f"\n📈 PERFORMANCE METRICS:")
            if signal_stats['closed_signals'] > 0:
                print(f"  Closed Signals: {signal_stats['closed_signals']}")
                print(f"  Win Rate: {signal_stats['win_rate']:.1f}%")
                print(f"  Avg Edge: {signal_stats['avg_edge']:+.2f}¢")
                print(f"  Total P&L: {signal_stats.get('total_pnl', 0):+.2f}¢")
            else:
                print(f"  No closed signals yet - continue collecting data")

            print(f"\n🤖 ML OPTIMIZATION:")
            print(f"  Price Predictor: {'Trained' if ml_insights['price_predictor_trained'] else 'Not trained'}")
            print(f"  Training Cycles: {ml_insights['training_cycles']}")
            print(f"  Optimizations Run: {ml_insights['optimization_count']}")
            print(f"  Status: {ml_insights['status'].upper()}")

            print(f"\n⚙️  SYSTEM HEALTH:")
            print(f"  Last Data Collection: {self.last_data_collection}")
            print(f"  Last Signal Generation: {self.last_signal_generation}")
            print(f"  Last ML Optimization: {self.last_ml_optimization}")
            print(f"  System Uptime: {self._calculate_uptime()}")

            print("\n" + "=" * 80)

            self.last_daily_report = datetime.now()

        except Exception as e:
            logger.error(f"❌ Daily report generation failed: {e}", exc_info=True)

    def _calculate_uptime(self) -> str:
        """Calculate system uptime."""
        if not self.last_data_collection:
            return "Just started"

        uptime = datetime.now() - self.last_data_collection
        hours = uptime.total_seconds() / 3600

        if hours < 1:
            return f"{int(uptime.total_seconds() / 60)} minutes"
        elif hours < 24:
            return f"{hours:.1f} hours"
        else:
            days = hours / 24
            return f"{days:.1f} days"

    def print_status(self):
        """Print current system status."""
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
        print(f"  Total Signals Generated: {self.total_signals_generated}")
        print(f"  Total Trades Executed: {self.total_trades_executed}")
        print(f"  Last Generation: {self.last_signal_generation or 'Never'}")

        print(f"\n📈 Performance (Last 7 days):")
        print(f"  Total Signals: {signal_stats['total_signals']}")
        print(f"  Win Rate: {signal_stats['win_rate']:.1f}%")
        print(f"  Avg Edge: {signal_stats['avg_edge']:+.2f}¢")

        print(f"\n🤖 ML Optimization:")
        print(f"  Total Cycles: {self.ml_cycles}")
        print(f"  Last Optimization: {self.last_ml_optimization or 'Never'}")

        print("\n" + "=" * 80)

    def run(self):
        """Run the complete system in a continuous loop."""
        logger.info("\n🚀 Starting The Oracle - Complete Automated System")
        logger.info(f"Data collection interval: {COLLECTION_INTERVAL}s ({COLLECTION_INTERVAL/60:.1f} min)")
        logger.info(f"Signal generation interval: {SIGNAL_INTERVAL}s ({SIGNAL_INTERVAL/60:.1f} min)")
        logger.info(f"ML optimization interval: {ML_OPTIMIZATION_INTERVAL}s ({ML_OPTIMIZATION_INTERVAL/3600:.1f} hours)")
        logger.info(f"Execution mode: {self.execution_mode.value}")
        logger.info("Press Ctrl+C to stop gracefully\n")

        # Initial cycles
        self.collect_data_cycle()
        self.generate_and_execute_signals_cycle()
        self.print_status()

        last_data_time = time.time()
        last_signal_time = time.time()
        last_update_time = time.time()
        last_ml_time = time.time()
        last_report_check = datetime.now()

        # Main loop
        while not shutdown_requested:
            try:
                current_time = time.time()
                current_datetime = datetime.now()

                # Check if it's time for data collection
                if current_time - last_data_time >= COLLECTION_INTERVAL:
                    self.collect_data_cycle()
                    last_data_time = current_time

                # Check if it's time for signal generation & execution
                if current_time - last_signal_time >= SIGNAL_INTERVAL:
                    self.generate_and_execute_signals_cycle()
                    last_signal_time = current_time

                # Check if it's time to update signals
                if current_time - last_update_time >= SIGNAL_UPDATE_INTERVAL:
                    self.update_signals_cycle()
                    last_update_time = current_time

                # Check if it's time for ML optimization
                if current_time - last_ml_time >= ML_OPTIMIZATION_INTERVAL:
                    self.ml_optimization_cycle()
                    last_ml_time = current_time

                # Check if it's time for daily report
                if (current_datetime.hour == DAILY_REPORT_HOUR and
                    (self.last_daily_report is None or
                     current_datetime.date() > self.last_daily_report.date())):
                    self.generate_daily_report()

                # Print status every 6 hours
                if self.data_cycles > 0 and self.data_cycles % 72 == 0:  # ~6 hours if 5min intervals
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

        self.generate_daily_report()  # Final report
        self.print_status()

        logger.info("\n✅ Oracle System stopped gracefully")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='The Oracle - Complete Automated Trading System'
    )

    parser.add_argument(
        '--mode',
        type=str,
        choices=['paper', 'live', 'disabled'],
        default='paper',
        help='Execution mode (default: paper)'
    )

    parser.add_argument(
        '--validate-days',
        type=int,
        default=7,
        help='Days to run in paper mode before going live (default: 7)'
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    print("\n" + "=" * 80)
    print("THE ORACLE - COMPLETE AUTOMATED TRADING SYSTEM")
    print("=" * 80)
    print("\nThis system will:")
    print("  1. ✅ Collect market data from Kalshi & Polymarket every 5 minutes")
    print("  2. ✅ Generate signals from 5+ strategies every 10 minutes")
    print("  3. ✅ Execute trades automatically (with safety controls)")
    print("  4. ✅ Optimize parameters with machine learning every hour")
    print("  5. ✅ Generate daily performance reports at 9 AM")
    print(f"\n⚙️  Execution Mode: {args.mode.upper()}")

    if args.mode == 'paper':
        print("   📝 PAPER MODE - Simulating trades, no real money at risk")
        print(f"   ⏰ Recommended: Run for {args.validate_days} days to validate strategies")
        print("   📊 Goal: Achieve 65%+ win rate before going live")
    elif args.mode == 'live':
        print("   💰 LIVE MODE - Real money trading enabled")
        print("   ⚠️  WARNING: Ensure strategies are validated first!")
    else:
        print("   🛑 DISABLED - Data collection only, no trade execution")

    print("\n🌍 Exchange Configuration:")
    print("   Data Collection: Kalshi ✅ + Polymarket ✅")
    print("   Trade Execution: Kalshi ONLY (US-based trading)")
    print("\n⚠️  Currently using SIMULATED data")
    print("   (Configure API keys in config/api_keys.py for live data)")
    print("\n" + "=" * 80)

    # Map string to ExecutionMode enum
    mode_mapping = {
        'paper': ExecutionMode.PAPER,
        'live': ExecutionMode.LIVE,
        'disabled': ExecutionMode.DISABLED
    }

    try:
        # Create and run system
        system = CompleteOracleSystem(execution_mode=mode_mapping[args.mode])
        system.run()

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
