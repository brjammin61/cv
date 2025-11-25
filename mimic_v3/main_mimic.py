#!/usr/bin/env python3
"""
MIMIC V3.1 - Central Cortex
The Main Async Orchestrator

Architecture:
┌─────────────────────────────────────────────────────────────┐
│                     MIMIC CORTEX                            │
├─────────────┬─────────────┬─────────────┬─────────────────── │
│   Scanner   │    Brain    │   Oracle    │   Risk Engine     │
│  (Whales)   │  (ML/River) │ (Sentiment) │ (Kelly + DDC)     │
├─────────────┴─────────────┴─────────────┴───────────────────┤
│                    Market Maker (LIP)                       │
├─────────────────────────────────────────────────────────────┤
│                   Kalshi Client (REST + WS)                 │
└─────────────────────────────────────────────────────────────┘

Flow:
1. Scanner detects whale activity → Signal
2. Oracle validates with news sentiment
3. Brain predicts win probability
4. Risk Engine calculates size
5. Execute trade or reject

Parallel:
- Maker runs LIP farming when not taking whale signals
"""

import os
import sys
import asyncio
import signal
import logging
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


def setup_logging(log_file: str = "logs/mimic_cortex.log") -> logging.Logger:
    """Configure logging for the system"""
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    # Console handler with colors
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    return logging.getLogger("CORTEX")


class MimicCortex:
    """
    Central orchestrator for MIMIC V3.1.

    Manages:
    - Dual-loop architecture (Taker + Maker)
    - Signal processing pipeline
    - Risk management
    - Graceful shutdown
    """

    def __init__(
        self,
        demo_mode: bool = False,
        paper_trading: bool = True,
        initial_capital: float = 1000.0
    ):
        load_dotenv()

        self.demo_mode = demo_mode
        self.paper_trading = paper_trading
        self.logger = setup_logging()

        self.logger.info("=" * 60)
        self.logger.info("MIMIC V3.1 CORTEX INITIALIZING")
        self.logger.info(f"Mode: {'DEMO' if demo_mode else 'PRODUCTION'}")
        self.logger.info(f"Trading: {'PAPER' if paper_trading else 'LIVE'}")
        self.logger.info("=" * 60)

        # Initialize components
        self.client: Optional[KalshiClient] = None
        self.risk_manager = InstitutionalRiskManager(
            capital=initial_capital,
            max_daily_loss=50.0,
            max_weekly_loss=150.0,
            kelly_fraction=0.25,
            logger=logging.getLogger("RISK")
        )
        self.brain = MimicBrain(
            model_path="models/brain_model.pkl",
            logger=logging.getLogger("BRAIN")
        )
        self.scanner = ShadowScanner(
            volume_threshold=500.0,
            logger=logging.getLogger("SCANNER")
        )
        self.oracle = NewsOracle(
            mock_mode=demo_mode,  # Use mock in demo mode
            logger=logging.getLogger("ORACLE")
        )
        self.maker = PassiveMarketMaker(
            logger=logging.getLogger("MAKER")
        )

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
        """Initialize all components and connections"""
        self.logger.info("Initializing components...")

        # Create Kalshi client
        api_key = os.getenv("KALSHI_API_KEY")
        api_secret = os.getenv("KALSHI_API_SECRET")

        if not api_key or not api_secret:
            self.logger.warning("No Kalshi API credentials found - running in simulation mode")
            self.paper_trading = True
        else:
            self.client = KalshiClient(
                api_key=api_key,
                api_secret=api_secret,
                demo_mode=self.demo_mode,
                logger=logging.getLogger("KALSHI")
            )
            await self.client.connect()

            # Set up scanner with client
            self.scanner.client = self.client
            self.maker.client = self.client

            # Set up WebSocket handlers
            if self.client:
                self.scanner.setup_websocket_handlers(self.client)

        # Create model directory
        os.makedirs("models", exist_ok=True)

        self.logger.info("Initialization complete")

    async def shutdown(self):
        """Graceful shutdown"""
        self.logger.info("Initiating shutdown...")
        self.running = False
        self.shutdown_event.set()

        # Cancel all maker quotes
        if self.maker:
            await self.maker.cancel_all_quotes()

        # Close connections
        if self.client:
            await self.client.close()

        if self.oracle:
            await self.oracle.close()

        # Save brain model
        if self.brain:
            self.brain._save_model()

        self.logger.info("Shutdown complete")

    async def handle_whale_signal(self, signal):
        """
        Process a whale signal through the full pipeline.

        Pipeline:
        1. Fast Lane: Resolution Arb (skip Oracle)
        2. Slow Lane: Informational (Oracle validation)
        3. Brain prediction
        4. Risk sizing
        5. Execution
        """
        self.stats["signals_processed"] += 1

        ticker = signal.ticker
        self.logger.info(f"WHALE SIGNAL: {signal.shadow_id} | {ticker} | {signal.strategy_type.value}")

        # 1. ORACLE CHECK (Slow Lane only)
        sentiment_score = 0.0
        if signal.strategy_type == StrategyType.INFORMATIONAL:
            try:
                oracle_result = await self.oracle.get_sentiment_snapshot(signal.raw_market_data)
                sentiment_score = oracle_result.score
                self.logger.info(f"  -> Oracle sentiment: {sentiment_score:.2f} ({oracle_result.summary[:50]})")
            except Exception as e:
                self.logger.warning(f"  -> Oracle error: {e}")

        # 2. FEATURE ENGINEERING & PREDICTION
        features = self.brain.extract_features(signal, sentiment_score)
        win_prob = self.brain.predict(features)
        self.logger.info(f"  -> Brain prediction: {win_prob:.1%} win probability")

        # 3. RISK ENGINE SIZING
        # Calculate payout ratio based on price
        # For binary at price P, payout_ratio = (1-P)/P for YES side
        price = signal.price
        if signal.side == "yes":
            payout_ratio = (1 - price) / price if price > 0 else 1.0
        else:
            payout_ratio = price / (1 - price) if price < 1 else 1.0

        size, reason = self.risk_manager.calculate_position_size(
            win_prob=win_prob,
            payout_ratio=payout_ratio,
            conviction=signal.confidence,
            estimation_samples=self.brain.whale_stats[signal.shadow_id].get("wins", 0) +
                              self.brain.whale_stats[signal.shadow_id].get("losses", 0) + 1,
            ticker=ticker,
            event_ticker=signal.event_ticker
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
        Execute a trade (paper or live).
        """
        ticker = signal.ticker
        side = OrderSide.YES if signal.side == "yes" else OrderSide.NO
        price_cents = int(signal.price * 100)
        contracts = max(1, int(size / signal.price))

        self.logger.info(
            f"  -> EXECUTING: {side.value.upper()} {ticker} | "
            f"{contracts} contracts @ {price_cents}c | ${size:.2f}"
        )

        if self.paper_trading or not self.client:
            # Paper trading simulation
            await self._simulate_trade(signal, size, features)
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

                # Track position
                self.risk_manager.open_position(
                    ticker=ticker,
                    event_ticker=signal.event_ticker,
                    side=signal.side,
                    price=signal.price,
                    size=size,
                    contracts=contracts
                )

            except Exception as e:
                self.logger.error(f"  -> Execution error: {e}")

        self.stats["trades_executed"] += 1

    async def _simulate_trade(self, signal, size: float, features: dict):
        """
        Simulate trade for paper trading mode.
        Uses a simple probabilistic model based on the signal quality.
        """
        import random

        # Wait a bit to simulate settlement
        await asyncio.sleep(0.5)

        # Simulate outcome based on confidence and strategy
        base_win_rate = 0.5

        # Arbitrage signals have higher base win rate
        if signal.strategy_type == StrategyType.ARBITRAGE:
            base_win_rate = 0.70

        # Adjust by confidence
        adjusted_rate = base_win_rate + (signal.confidence - 0.5) * 0.3

        is_win = random.random() < adjusted_rate

        # Calculate P&L
        if is_win:
            # Win pays out based on price
            pnl = size * ((1 - signal.price) / signal.price) * 0.9  # 10% fee approximation
        else:
            pnl = -size

        # Update systems
        self.risk_manager.update_equity(pnl)
        self.brain.learn(features, is_win, pnl)
        self.scanner.update_whale_outcome(signal.shadow_id, is_win, pnl)

        status = "WIN" if is_win else "LOSS"
        self.logger.info(f"  -> SETTLEMENT: {status} | PnL: ${pnl:.2f}")

    async def run_taker_loop(self):
        """
        Main taker loop - processes whale signals.
        """
        self.logger.info("TAKER LOOP: Starting whale detection")

        while self.running:
            try:
                # Check if trading is allowed
                can_trade, reason = self.risk_manager.can_trade()
                if not can_trade:
                    self.logger.warning(f"Trading paused: {reason}")
                    await asyncio.sleep(60)  # Wait before checking again
                    continue

                # Poll for signals
                signal = await self.scanner.poll_market_stream()

                if signal:
                    # Pause maker while processing signal
                    self.maker_active = False
                    await self.handle_whale_signal(signal)
                    self.maker_active = True

                await asyncio.sleep(0.5)  # 500ms polling interval

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Taker loop error: {e}")
                await asyncio.sleep(1)

        self.logger.info("TAKER LOOP: Stopped")

    async def run_maker_loop(self):
        """
        Main maker loop - runs LIP farming.
        """
        self.logger.info("MAKER LOOP: Starting LIP farming")

        if self.client:
            await self.maker.start()

        while self.running:
            try:
                if self.maker_active and self.maker.state.value == "ACTIVE":
                    status = await self.maker.run_lip_cycle()
                    self.logger.debug(f"Maker cycle: {status}")

                await asyncio.sleep(1)  # 1 second cycle

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Maker loop error: {e}")
                await asyncio.sleep(5)

        self.maker.stop()
        self.logger.info("MAKER LOOP: Stopped")

    async def run_websocket_loop(self):
        """
        WebSocket listener for real-time data.
        """
        if not self.client:
            self.logger.info("No client - skipping WebSocket loop")
            return

        self.logger.info("WEBSOCKET: Starting listener")

        try:
            # Subscribe to relevant channels
            await self.client.subscribe(
                channels=["trade", "orderbook_delta", "fill"],
                tickers=[]  # All markets
            )

            # This blocks until connection closes
            await self.client.start_websocket()

        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"WebSocket error: {e}")

        self.logger.info("WEBSOCKET: Stopped")

    async def run_status_loop(self):
        """
        Periodic status reporting.
        """
        while self.running:
            try:
                await asyncio.sleep(300)  # Every 5 minutes

                # Log status
                risk_status = self.risk_manager.get_status()
                brain_metrics = self.brain.get_metrics()

                self.logger.info("=" * 40)
                self.logger.info("STATUS REPORT")
                self.logger.info(f"  Capital: ${risk_status['capital']:.2f}")
                self.logger.info(f"  Drawdown: {risk_status['drawdown']:.1f}%")
                self.logger.info(f"  State: {risk_status['state']}")
                self.logger.info(f"  Signals: {self.stats['signals_processed']}")
                self.logger.info(f"  Trades: {self.stats['trades_executed']}")
                self.logger.info(f"  Brain Accuracy: {brain_metrics.get('accuracy', 0):.2%}")
                self.logger.info("=" * 40)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Status loop error: {e}")

    async def run_lifecycle(self):
        """
        Main entry point - runs all loops concurrently.
        """
        self.running = True
        self.stats["start_time"] = datetime.utcnow()

        # Set up signal handlers
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self.shutdown()))

        try:
            # Initialize
            await self.initialize()

            # Run all loops concurrently
            await asyncio.gather(
                self.run_taker_loop(),
                self.run_maker_loop(),
                self.run_websocket_loop(),
                self.run_status_loop(),
                return_exceptions=True
            )

        except Exception as e:
            self.logger.error(f"Lifecycle error: {e}")
        finally:
            await self.shutdown()


# ==================== ENTRY POINT ====================

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="MIMIC V3.1 Trading Cortex")
    parser.add_argument("--demo", action="store_true", help="Use demo API endpoints")
    parser.add_argument("--live", action="store_true", help="Enable live trading (not paper)")
    parser.add_argument("--capital", type=float, default=1000.0, help="Initial capital")

    args = parser.parse_args()

    cortex = MimicCortex(
        demo_mode=args.demo,
        paper_trading=not args.live,
        initial_capital=args.capital
    )

    try:
        asyncio.run(cortex.run_lifecycle())
    except KeyboardInterrupt:
        print("\nShutdown requested...")


if __name__ == "__main__":
    main()
