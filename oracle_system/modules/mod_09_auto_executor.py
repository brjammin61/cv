"""
Module 9: AutoExecutor

AUTOMATED TRADING ENGINE with comprehensive safety controls.

⚠️ CRITICAL: This module executes REAL TRADES with REAL MONEY.
Only enable after thorough validation and with explicit user approval.
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from enum import Enum

from connectors import KalshiConnector, PolymarketConnector
from modules import SignalTracker

logger = logging.getLogger(__name__)


class ExecutionMode(Enum):
    """Trading execution modes."""
    PAPER = "paper"           # Log only, no real trades
    LIVE = "live"             # Execute real trades
    DISABLED = "disabled"     # System off


class RiskLevel(Enum):
    """Risk assessment levels."""
    SAFE = "safe"
    ELEVATED = "elevated"
    HIGH = "high"
    CRITICAL = "critical"


class AutoExecutor:
    """
    Automated trade execution engine with comprehensive safety controls.

    This module can execute trades automatically when high-quality signals
    are detected. Includes multiple layers of safety controls and kill switches.
    """

    def __init__(
        self,
        mode: ExecutionMode = ExecutionMode.PAPER,
        max_position_size_usd: float = 100.0,
        max_total_exposure_usd: float = 500.0,
        min_edge_to_trade: float = 3.0,
        min_conviction: str = "HIGH",
        max_trades_per_day: int = 5,
        emergency_stop: bool = False,
        kalshi_connector=None
    ):
        """
        Initialize the auto-executor.

        Args:
            mode: Execution mode (PAPER, LIVE, DISABLED)
            max_position_size_usd: Maximum per-trade position size
            max_total_exposure_usd: Maximum total exposure across all positions
            min_edge_to_trade: Minimum edge (cents) to execute
            min_conviction: Minimum conviction level
            max_trades_per_day: Maximum trades per 24 hours
            emergency_stop: Emergency kill switch
            kalshi_connector: KalshiConnector instance for order placement
        """
        self.mode = mode
        self.max_position_size = max_position_size_usd
        self.max_total_exposure = max_total_exposure_usd
        self.min_edge = min_edge_to_trade
        self.min_conviction = min_conviction
        self.max_trades_per_day = max_trades_per_day
        self.emergency_stop = emergency_stop
        self.kalshi = kalshi_connector

        # Initialize trackers
        self.signal_tracker = SignalTracker()
        self.trades_today = 0
        self.current_exposure = 0.0
        self.last_reset = datetime.now().date()

        # Performance tracking
        self.total_trades = 0
        self.wins = 0
        self.losses = 0
        self.total_pnl = 0.0

        logger.info(f"AutoExecutor initialized in {mode.value.upper()} mode")
        if mode == ExecutionMode.LIVE:
            logger.warning("⚠️  LIVE TRADING MODE ENABLED - REAL MONEY AT RISK")

    def _reset_daily_limits(self):
        """Reset daily trade counter if new day."""
        today = datetime.now().date()
        if today > self.last_reset:
            logger.info(f"New trading day. Resetting daily counters.")
            self.trades_today = 0
            self.last_reset = today

    def _check_safety_conditions(self) -> Tuple[bool, str]:
        """
        Check all safety conditions before executing trade.

        Returns:
            (is_safe, reason)
        """
        # Emergency stop
        if self.emergency_stop:
            return False, "EMERGENCY STOP ACTIVATED"

        # Mode check
        if self.mode == ExecutionMode.DISABLED:
            return False, "System disabled"

        # Reset daily limits
        self._reset_daily_limits()

        # Daily trade limit
        if self.trades_today >= self.max_trades_per_day:
            return False, f"Daily trade limit reached ({self.max_trades_per_day})"

        # Exposure limit
        if self.current_exposure >= self.max_total_exposure:
            return False, f"Maximum exposure reached (${self.current_exposure:.2f})"

        return True, "All safety checks passed"

    def _assess_risk_level(self, signal: Dict) -> RiskLevel:
        """
        Assess risk level of a potential trade.

        Args:
            signal: Signal dictionary

        Returns:
            RiskLevel
        """
        edge = signal.get('edge_cents', 0)
        conviction = signal.get('conviction', 'LOW')
        market_liquidity = signal.get('liquidity', 0)

        # Calculate risk score
        risk_score = 0

        # Edge contributes to safety
        if edge >= 5.0:
            risk_score -= 2
        elif edge >= 3.0:
            risk_score -= 1
        elif edge < 2.0:
            risk_score += 2

        # Conviction contributes to safety
        if conviction == "HIGH":
            risk_score -= 2
        elif conviction == "MEDIUM":
            risk_score += 0
        else:
            risk_score += 3

        # Liquidity matters
        if market_liquidity < 10000:
            risk_score += 2
        elif market_liquidity > 100000:
            risk_score -= 1

        # Determine risk level
        if risk_score <= -2:
            return RiskLevel.SAFE
        elif risk_score <= 0:
            return RiskLevel.ELEVATED
        elif risk_score <= 2:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL

    def _calculate_position_size(
        self,
        signal: Dict,
        risk_level: RiskLevel
    ) -> float:
        """
        Calculate optimal position size based on edge, conviction, and risk.

        Uses a simplified approach: base size scales with edge and conviction,
        then adjusted for risk level.

        Args:
            signal: Signal dictionary
            risk_level: Assessed risk level

        Returns:
            Position size in USD
        """
        edge_cents = signal.get('edge_cents', 0)
        conviction = signal.get('conviction', 'MEDIUM')

        if edge_cents <= 0:
            return 0.0

        # Base position size: scale with edge
        # 3¢ edge = $15, 5¢ = $25, 10¢ = $50 (max)
        # Formula: base = min($15 + (edge - 3) * 3.5, max_position_size)
        base_size = min(15.0 + (edge_cents - 3.0) * 3.5, self.max_position_size)

        # Conviction multiplier
        conviction_multipliers = {
            "NONE": 0.0,
            "LOW": 0.5,
            "MEDIUM": 0.7,
            "HIGH": 1.0
        }
        base_size *= conviction_multipliers.get(conviction, 0.7)

        # Adjust for risk level
        risk_multipliers = {
            RiskLevel.SAFE: 1.0,
            RiskLevel.ELEVATED: 0.8,
            RiskLevel.HIGH: 0.5,
            RiskLevel.CRITICAL: 0.0
        }

        adjusted_size = base_size * risk_multipliers[risk_level]

        # Apply hard limits
        position_size = min(
            adjusted_size,
            self.max_position_size,
            self.max_total_exposure - self.current_exposure
        )

        return max(0, position_size)

    def should_execute_signal(self, signal: Dict) -> Tuple[bool, str, float]:
        """
        Determine if a signal should be executed.

        Args:
            signal: Signal dictionary

        Returns:
            (should_execute, reason, position_size)
        """
        # Check safety conditions
        is_safe, safety_reason = self._check_safety_conditions()
        if not is_safe:
            return False, safety_reason, 0.0

        # Check signal quality
        edge = signal.get('edge_cents', 0)
        conviction = signal.get('conviction', 'NONE')

        if edge < self.min_edge:
            return False, f"Edge too small ({edge:.2f}¢ < {self.min_edge:.2f}¢)", 0.0

        conviction_levels = {"NONE": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3}
        min_conviction_level = conviction_levels.get(self.min_conviction, 2)
        signal_conviction_level = conviction_levels.get(conviction, 0)

        if signal_conviction_level < min_conviction_level:
            return False, f"Conviction too low ({conviction} < {self.min_conviction})", 0.0

        # Assess risk
        risk_level = self._assess_risk_level(signal)

        if risk_level == RiskLevel.CRITICAL:
            return False, "Risk level CRITICAL - trade rejected", 0.0

        # Calculate position size
        position_size = self._calculate_position_size(signal, risk_level)

        if position_size < 10:  # Minimum $10 position
            return False, f"Position size too small (${position_size:.2f})", 0.0

        # All checks passed
        reason = f"✅ Approved: Edge={edge:.2f}¢, Conviction={conviction}, Risk={risk_level.value}, Size=${position_size:.2f}"
        return True, reason, position_size

    def execute_trade(
        self,
        signal: Dict,
        position_size: float
    ) -> Optional[Dict]:
        """
        Execute a trade based on signal.

        Args:
            signal: Signal dictionary
            position_size: Position size in USD

        Returns:
            Trade result dictionary or None
        """
        if self.mode == ExecutionMode.DISABLED:
            logger.warning("Cannot execute - system disabled")
            return None

        signal_type = signal.get('signal_type', 'UNKNOWN')
        market_name = signal.get('market_name', 'Unknown')
        edge = signal.get('edge_cents', 0)

        if self.mode == ExecutionMode.PAPER:
            # Paper trading - simulated orders for tracking outcomes
            logger.info(
                f"📝 PAPER TRADE: {signal_type} on {market_name} "
                f"(${position_size:.2f}, edge={edge:.2f}¢)"
            )

            # Determine side: BUY signal = YES, SELL signal = NO
            side = "yes" if signal_type.upper() == "BUY" else "no"

            # Calculate number of contracts
            market_price_cents = int(signal.get('market_price', 0.5) * 100)
            if market_price_cents == 0:
                market_price_cents = 5000  # Default to 50 cents

            num_contracts = int((position_size * 100) / market_price_cents)
            if num_contracts < 1:
                num_contracts = 1  # Minimum 1 contract for paper trading

            # Place paper order if Kalshi connector available
            order_result = None
            if self.kalshi:
                ticker = signal.get('market_ticker') or signal.get('market_id', '')
                if ticker:
                    order_result = self.kalshi.place_order(
                        ticker=ticker,
                        side=side,
                        count=num_contracts,
                        price_cents=market_price_cents,
                        paper_mode=True  # PAPER ORDER
                    )

            # Log to signal tracker
            signal_id = self.signal_tracker.log_signal(
                strategy=signal.get('strategy', 'Unknown'),
                market_name=market_name,
                signal_type=signal_type,
                edge_cents=edge,
                conviction=signal.get('conviction', 'MEDIUM'),
                market_price=signal.get('market_price'),
                rationale=signal.get('rationale', 'Auto-executed paper trade'),
                metadata={
                    'mode': 'paper',
                    'position_size_usd': position_size,
                    'contracts': num_contracts,
                    'order_id': order_result['order_id'] if order_result else None
                }
            )

            # Update tracking (even for paper trades)
            self.trades_today += 1
            self.total_trades += 1

            return {
                'signal_id': signal_id,
                'mode': 'paper',
                'executed': True,
                'position_size': position_size,
                'contracts': num_contracts,
                'order_id': order_result['order_id'] if order_result else None
            }

        elif self.mode == ExecutionMode.LIVE:
            # LIVE TRADING - REAL MONEY
            logger.warning(
                f"💰 LIVE TRADE: {signal_type} on {market_name} "
                f"(${position_size:.2f}, edge={edge:.2f}¢)"
            )

            if not self.kalshi:
                logger.error("❌ No Kalshi connector available for LIVE trading")
                return None

            # Determine side: BUY signal = YES, SELL signal = NO
            side = "yes" if signal_type.upper() == "BUY" else "no"

            # Calculate number of contracts
            # Position size is in USD, each contract costs market_price
            market_price_cents = int(signal.get('market_price', 0.5) * 100)
            if market_price_cents == 0:
                market_price_cents = 5000  # Default to 50 cents if unknown

            num_contracts = int((position_size * 100) / market_price_cents)
            if num_contracts < 1:
                logger.warning(f"Position size too small for even 1 contract")
                return None

            # Place order via Kalshi
            ticker = signal.get('market_ticker') or signal.get('market_id', '')
            if not ticker:
                logger.error("❌ No market ticker available")
                return None

            order_result = self.kalshi.place_order(
                ticker=ticker,
                side=side,
                count=num_contracts,
                price_cents=market_price_cents,
                paper_mode=False  # REAL ORDER
            )

            if order_result:
                # Log to signal tracker
                signal_id = self.signal_tracker.log_signal(
                    strategy=signal.get('strategy', 'Unknown'),
                    market_name=market_name,
                    signal_type=signal_type,
                    edge_cents=edge,
                    conviction=signal.get('conviction', 'MEDIUM'),
                    market_price=signal.get('market_price'),
                    rationale=f"Auto-executed LIVE: {order_result['order_id']}",
                    metadata={
                        'mode': 'live',
                        'position_size_usd': position_size,
                        'order_id': order_result['order_id'],
                        'contracts': num_contracts
                    }
                )

                # Update exposure tracking
                self.current_exposure += position_size
                self.trades_today += 1
                self.total_trades += 1

                logger.info(f"✅ LIVE order placed successfully: {order_result['order_id']}")

                return {
                    'signal_id': signal_id,
                    'mode': 'live',
                    'executed': True,
                    'position_size': position_size,
                    'order_id': order_result['order_id'],
                    'contracts': num_contracts
                }
            else:
                logger.error("❌ Failed to place LIVE order")
                return None

    def emergency_shutdown(self):
        """
        Emergency shutdown - stops all trading immediately.
        """
        logger.critical("🚨 EMERGENCY SHUTDOWN ACTIVATED")
        self.emergency_stop = True
        self.mode = ExecutionMode.DISABLED

        # TODO: Close all open positions if needed

        logger.critical("All trading stopped. Manual intervention required.")

    def get_status(self) -> Dict:
        """Get current executor status."""
        return {
            'mode': self.mode.value,
            'emergency_stop': self.emergency_stop,
            'trades_today': self.trades_today,
            'max_trades_per_day': self.max_trades_per_day,
            'current_exposure': self.current_exposure,
            'max_exposure': self.max_total_exposure,
            'total_trades': self.total_trades,
            'wins': self.wins,
            'losses': self.losses,
            'win_rate': (self.wins / self.total_trades * 100) if self.total_trades > 0 else 0,
            'total_pnl': self.total_pnl
        }

    def print_status(self):
        """Print formatted status report."""
        status = self.get_status()

        print("\n" + "=" * 80)
        print("AUTO-EXECUTOR STATUS")
        print("=" * 80)

        print(f"\n🔧 Mode: {status['mode'].upper()}")
        if status['emergency_stop']:
            print("🚨 EMERGENCY STOP: ACTIVE")

        print(f"\n📊 Today's Activity:")
        print(f"  Trades: {status['trades_today']} / {status['max_trades_per_day']}")
        print(f"  Exposure: ${status['current_exposure']:.2f} / ${status['max_exposure']:.2f}")

        print(f"\n📈 All-Time Performance:")
        print(f"  Total Trades: {status['total_trades']}")
        print(f"  Wins: {status['wins']}")
        print(f"  Losses: {status['losses']}")
        print(f"  Win Rate: {status['win_rate']:.1f}%")
        print(f"  Total P&L: ${status['total_pnl']:.2f}")

        print("\n" + "=" * 80)


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 80)
    print("AUTO-EXECUTOR - Module 9")
    print("=" * 80)

    # Initialize in PAPER mode (safe for testing)
    executor = AutoExecutor(
        mode=ExecutionMode.PAPER,
        max_position_size_usd=100,
        max_total_exposure_usd=500,
        min_edge_to_trade=3.0,
        min_conviction="HIGH"
    )

    # Example signal
    test_signal = {
        'strategy': 'SpatialArbitrage',
        'market_name': 'Test Market',
        'signal_type': 'BUY',
        'edge_cents': 4.5,
        'conviction': 'HIGH',
        'market_price': 0.48,
        'rationale': 'Strong arbitrage opportunity',
        'liquidity': 150000
    }

    print("\n[1] Evaluating test signal...")
    should_execute, reason, position_size = executor.should_execute_signal(test_signal)

    print(f"Decision: {'✅ EXECUTE' if should_execute else '❌ REJECT'}")
    print(f"Reason: {reason}")
    if should_execute:
        print(f"Position Size: ${position_size:.2f}")

        print("\n[2] Executing trade (paper mode)...")
        result = executor.execute_trade(test_signal, position_size)
        print(f"Result: {result}")

    print("\n[3] Current status:")
    executor.print_status()

    print("\n⚠️  To enable LIVE trading:")
    print("  1. Thoroughly validate system on paper trades")
    print("  2. Set mode=ExecutionMode.LIVE")
    print("  3. Implement actual exchange API calls")
    print("  4. Add additional safety reviews")
