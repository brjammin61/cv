#!/usr/bin/env python3
"""
MIMIC V3.1 HARDENED - Central Cortex
The Main Async Orchestrator with Persistence

Architecture:
┌─────────────────────────────────────────────────────────────┐
│                     MIMIC CORTEX                            │
├─────────────────────────────────────────────────────────────┤
│                      PERSISTENCE (SQLite)                   │
├─────────────┬─────────────┬─────────────┬──────────────────┤
│   Scanner   │    Brain    │   Oracle    │   Risk Engine    │
│  (Whales)   │  (ML/River) │ (Sentiment) │ (Kelly + DDC)    │
├─────────────┴─────────────┴─────────────┴──────────────────┤
│                    Market Maker (LIP)                       │
├─────────────────────────────────────────────────────────────┤
│                   Kalshi Client (REST + WS)                 │
└─────────────────────────────────────────────────────────────┘

HARDENED Features:
- SQLite persistence for Shadow IDs and trades
- State recovery after crash/restart
- Position tracking survives reboots
- Asymptotic Kelly with variance adjustment
- LIP optimization and inventory skew
"""

import os
import sys
import asyncio
import signal
import logging
import uuid
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

# Add modules to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.mimic_v3.kalshi_client import KalshiClient, OrderSide, OrderType
from modules.mimic_v3.scanner import ShadowScanner, StrategyType
from modules.mimic_v3.brain import MimicBrain
from modules.mimic_v3.risk_engine import InstitutionalRiskManager
from modules.mimic_v3.news_oracle import NewsOracle
from modules.mimic_v3.maker import PassiveMarketMaker
from modules.mimic_v3.persistence import MimicDB

# Dashboard imports (optional)
try:
    from dashboard import dashboard_state, app as dashboard_app
    import uvicorn
    DASHBOARD_AVAILABLE = True
except ImportError:
    DASHBOARD_AVAILABLE = False


def setup_logging(log_file: str = "logs/mimic_cortex.log") -> logging.Logger:
    """Configure logging for the system"""
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    return logging.getLogger("CORTEX")


class MimicCortex:
    """
    HARDENED Central Orchestrator for MIMIC V3.1.

    Features:
    - Dual-loop architecture (Taker + Maker)
    - SQLite persistence layer
    - State recovery after restart
    - Signal processing pipeline
    - Graceful shutdown with state save
    """

    def __init__(
        self,
        demo_mode: bool = False,
        paper_trading: bool = True,
        initial_capital: float = 1000.0,
        db_path: str = "data/mimic_data.db",
        dashboard_port: int = 8080,
        enable_dashboard: bool = True
    ):
        load_dotenv()

        self.demo_mode = demo_mode
        self.paper_trading = paper_trading
        self.initial_capital = initial_capital
        self.db_path = db_path
        self.dashboard_port = dashboard_port
        self.enable_dashboard = enable_dashboard and DASHBOARD_AVAILABLE
        self.logger = setup_logging()

        self.logger.info("=" * 60)
        self.logger.info("MIMIC V3.1 HARDENED - CORTEX INITIALIZING")
        self.logger.info(f"Mode: {'DEMO' if demo_mode else 'PRODUCTION'}")
        self.logger.info(f"Trading: {'PAPER' if paper_trading else 'LIVE'}")
        self.logger.info(f"Database: {db_path}")
        self.logger.info(f"Dashboard: {'ENABLED' if self.enable_dashboard else 'DISABLED'}")
        self.logger.info("=" * 60)

        # Initialize persistence FIRST
        self.db: Optional[MimicDB] = None

        # Initialize components (will be wired up in initialize())
        self.client: Optional[KalshiClient] = None
        self.risk_manager: Optional[InstitutionalRiskManager] = None
        self.brain: Optional[MimicBrain] = None
        self.scanner: Optional[ShadowScanner] = None
        self.oracle: Optional[NewsOracle] = None
        self.maker: Optional[PassiveMarketMaker] = None

        # State
        self.running = False
        self.maker_active = True
        self.shutdown_event = asyncio.Event()

        # Statistics
        self.stats = {
            "start_time": None,
            "signals_processed": 0,
            "trades_executed": 0,
            "trades_rejected": 0
        }

    async def initialize(self):
        """Initialize all components with persistence"""
        self.logger.info("Initializing components...")

        # Create directories
        os.makedirs("data", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        os.makedirs("models", exist_ok=True)

        # 1. Initialize persistence layer
        self.db = MimicDB(
            db_path=self.db_path,
            logger=logging.getLogger("DB")
        )
        self.logger.info(f"Database initialized: {self.db.get_db_stats()}")

        # 2. Initialize Risk Manager with persistence
        self.risk_manager = InstitutionalRiskManager(
            capital=self.initial_capital,
            max_daily_loss=50.0,
            max_weekly_loss=150.0,
            kelly_fraction=0.25,
            db=self.db,
            logger=logging.getLogger("RISK")
        )

        # 3. Initialize Brain
        self.brain = MimicBrain(
            model_path="models/brain_model.pkl",
            logger=logging.getLogger("BRAIN")
        )

        # 4. Initialize Scanner with persistence
        self.scanner = ShadowScanner(
            db=self.db,
            volume_threshold=500.0,
            logger=logging.getLogger("SCANNER")
        )

        # 5. Initialize Oracle
        self.oracle = NewsOracle(
            mock_mode=self.demo_mode,
            logger=logging.getLogger("ORACLE")
        )

        # 6. Initialize Maker with persistence
        self.maker = PassiveMarketMaker(
            db=self.db,
            logger=logging.getLogger("MAKER")
        )

        # 7. Create Kalshi client if credentials available
        api_key = os.getenv("KALSHI_API_KEY")
        api_secret = os.getenv("KALSHI_API_SECRET")

        if not api_key or not api_secret:
            self.logger.warning("No Kalshi API credentials - running in simulation mode")
            self.paper_trading = True
        else:
            self.client = KalshiClient(
                api_key=api_key,
                api_secret=api_secret,
                demo_mode=self.demo_mode,
                logger=logging.getLogger("KALSHI")
            )
            await self.client.connect()

            # Wire up client to components
            self.scanner.client = self.client
            self.maker.client = self.client
            self.scanner.setup_websocket_handlers(self.client)

        # Log recovered state
        open_positions = self.db.get_open_positions()
        if open_positions:
            self.logger.info(f"Recovered {len(open_positions)} open positions")

        db_stats = self.db.get_db_stats()
        self.logger.info(f"Database: {db_stats['total_whales']} whales, {db_stats['total_trades']} trades")

        # 8. Connect dashboard to engine components
        if self.enable_dashboard:
            dashboard_state.connect_engine(
                risk_manager=self.risk_manager,
                scanner=self.scanner,
                maker=self.maker,
                brain=self.brain,
                db=self.db,
                client=self.client
            )
            self.logger.info(f"Dashboard connected - will serve on port {self.dashboard_port}")

        self.logger.info("Initialization complete")

    async def shutdown(self):
        """Graceful shutdown with state persistence"""
        self.logger.info("Initiating shutdown...")
        self.running = False
        self.shutdown_event.set()

        # Cancel all maker quotes
        if self.maker:
            await self.maker.cancel_all_quotes()

        # Save daily snapshot
        if self.db and self.risk_manager:
            status = self.risk_manager.get_status()
            self.db.save_daily_snapshot(
                starting_capital=self.initial_capital,
                ending_capital=status['capital'],
                daily_pnl=status['daily_pnl'],
                trades_taken=status['daily_trades'],
                wins=status['stats']['winning_trades'],
                losses=status['stats']['losing_trades'],
                max_drawdown=status['stats']['max_drawdown_pct']
            )

        # Close connections
        if self.client:
            await self.client.close()

        if self.oracle:
            await self.oracle.close()

        # Save brain model
        if self.brain:
            self.brain._save_model()

        # Close database
        if self.db:
            self.db.close()

        self.logger.info("Shutdown complete")

    async def handle_whale_signal(self, signal):
        """
        Process a whale signal through the full pipeline.

        HARDENED: Logs all trades to database.
        """
        self.stats["signals_processed"] += 1

        ticker = signal.ticker
        self.logger.info(
            f"WHALE SIGNAL: {signal.shadow_id} | {ticker} | "
            f"{signal.strategy_type.value} | Conf: {signal.confidence:.0%}"
        )

        # 1. ORACLE CHECK (Slow Lane only)
        sentiment_score = 0.0
        if signal.strategy_type == StrategyType.INFORMATIONAL:
            try:
                oracle_result = await self.oracle.get_sentiment_snapshot(signal.raw_market_data)
                sentiment_score = oracle_result.score
                self.logger.info(f"  -> Oracle: {sentiment_score:+.2f} | {oracle_result.summary[:50]}")
            except Exception as e:
                self.logger.warning(f"  -> Oracle error: {e}")

        # 2. FEATURE ENGINEERING & PREDICTION
        features = self.brain.extract_features(signal, sentiment_score)
        win_prob = self.brain.predict(features)
        self.logger.info(f"  -> Brain: {win_prob:.1%} win probability")

        # 3. RISK ENGINE SIZING
        price = signal.price
        if signal.side == "yes":
            payout_ratio = (1 - price) / price if price > 0 else 1.0
        else:
            payout_ratio = price / (1 - price) if price < 1 else 1.0

        # Get whale trade count for estimation samples
        whale_stats = self.brain.whale_stats.get(signal.shadow_id, {})
        estimation_samples = whale_stats.get("wins", 0) + whale_stats.get("losses", 0) + 1

        # Get resolution time for time-horizon weighting
        resolution_hours = getattr(signal, 'resolution_proximity', None)

        size, reason = self.risk_manager.calculate_position_size(
            win_prob=win_prob,
            payout_ratio=payout_ratio,
            conviction=signal.confidence,
            estimation_samples=estimation_samples,
            ticker=ticker,
            event_ticker=signal.event_ticker,
            resolution_hours=resolution_hours
        )

        if size <= 0:
            self.logger.info(f"  -> REJECTED: {reason}")
            self.stats["trades_rejected"] += 1
            return

        self.logger.info(f"  -> Risk approved: ${size:.2f}")

        # 4. EXECUTION
        await self.execute_trade(signal, size, features, win_prob)

    async def execute_trade(self, signal, size: float, features: dict, win_prob: float):
        """
        Execute a trade with full persistence.
        """
        ticker = signal.ticker
        side = OrderSide.YES if signal.side == "yes" else OrderSide.NO
        price_cents = int(signal.price * 100)
        contracts = max(1, int(size / signal.price))

        # Generate trade ID
        trade_id = f"MIMIC_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"

        self.logger.info(
            f"  -> EXECUTING: {side.value.upper()} {ticker} | "
            f"{contracts} contracts @ {price_cents}c | ${size:.2f} | ID: {trade_id}"
        )

        if self.paper_trading or not self.client:
            # Paper trading simulation
            await self._simulate_trade(trade_id, signal, size, features)
        else:
            # Live execution
            try:
                order_response = await self.client.create_order(
                    ticker=ticker,
                    side=side,
                    order_type=OrderType.LIMIT,
                    count=contracts,
                    price=price_cents
                )

                order_id = order_response.get("order", {}).get("order_id")
                self.logger.info(f"  -> Order placed: {order_id}")

                # Track position with persistence
                self.risk_manager.open_position(
                    trade_id=trade_id,
                    ticker=ticker,
                    event_ticker=signal.event_ticker,
                    side=signal.side,
                    price=signal.price,
                    size=size,
                    contracts=contracts,
                    shadow_id=signal.shadow_id,
                    strategy_type=signal.strategy_type.value,
                    win_prob=win_prob
                )

            except Exception as e:
                self.logger.error(f"  -> Execution error: {e}")
                return

        self.stats["trades_executed"] += 1

    async def _simulate_trade(self, trade_id: str, signal, size: float, features: dict):
        """
        Paper trading mode - OPEN position only, NO FAKE SETTLEMENT.

        FIXED: Previously this would randomly settle trades after 0.5s,
        causing the dashboard to flash with fake wins/losses.

        Now we just log the position as OPEN and wait for real market settlement.
        """
        # Open position in risk manager (persisted to DB as OPEN)
        self.risk_manager.open_position(
            trade_id=trade_id,
            ticker=signal.ticker,
            event_ticker=signal.event_ticker,
            side=signal.side,
            price=signal.price,
            size=size,
            contracts=int(size / signal.price),
            shadow_id=signal.shadow_id,
            strategy_type=signal.strategy_type.value,
            win_prob=self.brain.predict(features)
        )

        self.logger.info(f"  -> POSITION OPEN: {signal.ticker} | Waiting for real settlement...")

        # ═══════════════════════════════════════════════════════════════════
        # CRITICAL FIX: DO NOT SIMULATE SETTLEMENT
        # ═══════════════════════════════════════════════════════════════════
        # In Paper Trading mode, we do NOT know the outcome yet.
        # The position stays OPEN until the real market settles.
        #
        # Previously this code would:
        #   await asyncio.sleep(0.5)
        #   is_win = random.random() < adjusted_rate
        #   self.risk_manager.close_position(...)
        #
        # This caused 10,000+ fake trades/hour flashing on the dashboard.
        # ═══════════════════════════════════════════════════════════════════

    async def run_taker_loop(self):
        """Main taker loop - processes whale signals"""
        self.logger.info("TAKER LOOP: Starting")

        while self.running:
            try:
                can_trade, reason = self.risk_manager.can_trade()
                if not can_trade:
                    self.logger.warning(f"Trading paused: {reason}")
                    await asyncio.sleep(60)
                    continue

                signal = await self.scanner.poll_market_stream()

                if signal:
                    self.maker_active = False
                    await self.handle_whale_signal(signal)
                    self.maker_active = True

                # Slower polling to avoid API rate limits (every 5 seconds)
                await asyncio.sleep(5.0)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Taker loop error: {e}")
                await asyncio.sleep(1)

        self.logger.info("TAKER LOOP: Stopped")

    async def run_maker_loop(self):
        """Main maker loop - runs LIP farming"""
        self.logger.info("MAKER LOOP: Starting")

        if self.client:
            await self.maker.start()

        while self.running:
            try:
                if self.maker_active and self.maker.state.value == "ACTIVE":
                    status = await self.maker.run_lip_cycle()
                    self.logger.debug(f"Maker cycle: {status}")

                await asyncio.sleep(1)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Maker loop error: {e}")
                await asyncio.sleep(5)

        self.maker.stop()
        self.logger.info("MAKER LOOP: Stopped")

    async def run_websocket_loop(self):
        """WebSocket listener for real-time data"""
        if not self.client:
            self.logger.info("No client - skipping WebSocket loop")
            return

        self.logger.info("WEBSOCKET: Starting")

        try:
            await self.client.subscribe(
                channels=["trade", "orderbook_delta", "fill"],
                tickers=[]
            )
            await self.client.start_websocket()

        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"WebSocket error: {e}")

        self.logger.info("WEBSOCKET: Stopped")

    async def run_settlement_loop(self):
        """
        Settlement Loop - Checks for resolved markets and closes positions.

        Runs every 60 seconds to:
        1. Get all open positions from database
        2. Check each market's status via Kalshi API
        3. Close positions when markets settle
        """
        self.logger.info("SETTLEMENT LOOP: Starting")

        while self.running:
            try:
                await asyncio.sleep(60)  # Check every minute

                if not self.client:
                    continue  # Can't check settlements without API

                # Get open positions from risk manager
                open_positions = list(self.risk_manager.positions.items())

                if not open_positions:
                    continue

                self.logger.debug(f"SETTLEMENT: Checking {len(open_positions)} open positions")

                for ticker, position in open_positions:
                    try:
                        # Get market status from Kalshi
                        market = await self.client.get_market(ticker)
                        market_data = market.get("market", {})
                        status = market_data.get("status", "open")
                        result = market_data.get("result", None)  # "yes" or "no" when settled

                        if status == "settled" and result:
                            # Market has settled - close position
                            exit_price = 1.0 if result == "yes" else 0.0
                            pnl = self.risk_manager.close_position(ticker, exit_price)

                            if pnl is not None:
                                # Update brain with outcome for learning
                                is_win = pnl > 0
                                self.brain.update_whale_stats(
                                    position.shadow_id,
                                    is_win,
                                    pnl
                                )

                                self.logger.info(
                                    f"SETTLEMENT: {ticker} -> {result.upper()} | "
                                    f"PnL: ${pnl:+.2f} | Side: {position.side}"
                                )

                        elif status == "closed":
                            # Market closed but not yet settled - check close_time
                            close_time = market_data.get("close_time")
                            if close_time:
                                from datetime import datetime
                                close_dt = datetime.fromisoformat(close_time.replace("Z", "+00:00"))
                                if datetime.now(close_dt.tzinfo) > close_dt:
                                    # Market is past close time, mark as expired if >24h old
                                    hours_past = (datetime.utcnow() - close_dt.replace(tzinfo=None)).total_seconds() / 3600
                                    if hours_past > 24:
                                        self.logger.warning(f"SETTLEMENT: {ticker} expired (closed >24h ago)")
                                        # Expire the position at break-even
                                        self.risk_manager.close_position(ticker, position.entry_price)

                    except Exception as e:
                        self.logger.debug(f"SETTLEMENT: Error checking {ticker}: {e}")
                        continue

                    # Rate limiting - don't hammer the API
                    await asyncio.sleep(0.5)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Settlement loop error: {e}")
                await asyncio.sleep(30)

        self.logger.info("SETTLEMENT LOOP: Stopped")

    async def run_status_loop(self):
        """Periodic status reporting"""
        while self.running:
            try:
                await asyncio.sleep(300)  # Every 5 minutes

                risk_status = self.risk_manager.get_status()
                brain_metrics = self.brain.get_metrics()
                scanner_stats = self.scanner.get_stats()
                db_stats = self.db.get_db_stats()

                self.logger.info("=" * 50)
                self.logger.info("STATUS REPORT")
                self.logger.info(f"  Capital: ${risk_status['capital']:.2f} ({risk_status['state']})")
                self.logger.info(f"  Drawdown: {risk_status['drawdown_pct']:.1f}%")
                self.logger.info(f"  Daily PnL: ${risk_status['daily_pnl']:+.2f}")
                self.logger.info(f"  Signals: {self.stats['signals_processed']}")
                self.logger.info(f"  Trades: {self.stats['trades_executed']}")
                self.logger.info(f"  Brain Accuracy: {brain_metrics.get('accuracy', 0):.1%}")
                self.logger.info(f"  Whales Tracked: {scanner_stats['unique_whales']}")
                self.logger.info(f"  DB: {db_stats['total_trades']} trades, {db_stats['total_whales']} whales")
                self.logger.info("=" * 50)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Status loop error: {e}")

    async def run_dashboard_server(self):
        """Run the Bloomberg-style dashboard server"""
        if not self.enable_dashboard:
            self.logger.info("Dashboard disabled - skipping")
            return

        self.logger.info(f"DASHBOARD: Starting on http://0.0.0.0:{self.dashboard_port}")

        config = uvicorn.Config(
            dashboard_app,
            host="0.0.0.0",
            port=self.dashboard_port,
            log_level="warning",
            access_log=False
        )
        server = uvicorn.Server(config)

        try:
            await server.serve()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Dashboard server error: {e}")

        self.logger.info("DASHBOARD: Stopped")

    async def run_lifecycle(self):
        """Main entry point - runs all loops concurrently"""
        self.running = True
        self.stats["start_time"] = datetime.utcnow()

        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self.shutdown()))

        try:
            await self.initialize()

            await asyncio.gather(
                self.run_taker_loop(),
                self.run_maker_loop(),
                self.run_websocket_loop(),
                self.run_settlement_loop(),
                self.run_status_loop(),
                self.run_dashboard_server(),
                return_exceptions=True
            )

        except Exception as e:
            self.logger.error(f"Lifecycle error: {e}")
        finally:
            await self.shutdown()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="MIMIC V3.1 HARDENED Trading Cortex")
    parser.add_argument("--demo", action="store_true", help="Use demo API endpoints")
    parser.add_argument("--live", action="store_true", help="Enable live trading")
    parser.add_argument("--capital", type=float, default=1000.0, help="Initial capital")
    parser.add_argument("--db", type=str, default="data/mimic_data.db", help="Database path")
    parser.add_argument("--dashboard-port", type=int, default=8080, help="Dashboard server port")
    parser.add_argument("--no-dashboard", action="store_true", help="Disable dashboard")

    args = parser.parse_args()

    cortex = MimicCortex(
        demo_mode=args.demo,
        paper_trading=not args.live,
        initial_capital=args.capital,
        db_path=args.db,
        dashboard_port=args.dashboard_port,
        enable_dashboard=not args.no_dashboard
    )

    try:
        asyncio.run(cortex.run_lifecycle())
    except KeyboardInterrupt:
        print("\nShutdown requested...")


if __name__ == "__main__":
    main()
