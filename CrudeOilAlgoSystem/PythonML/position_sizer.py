"""
Dynamic Position Sizing Engine
================================

Intelligently scales position size (1-3 contracts) based on:
1. Market regime (HMM detector)
2. Current volatility (ATR)
3. Account equity and risk limits
4. Recent performance (winning/losing streak)

This is THE KEY to safely scaling from $3k/month to $10k/month.

Author: Algorithmic Trading Framework 2025
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple
from datetime import datetime


class DynamicPositionSizer:
    """
    Calculates optimal position size based on multiple factors
    """

    def __init__(self,
                 account_size: float = 50000,
                 max_contracts: int = 3,
                 risk_per_trade_pct: float = 0.02,
                 max_daily_risk_pct: float = 0.05):
        """
        Initialize position sizer

        Args:
            account_size: Starting account balance ($)
            max_contracts: Maximum contracts to trade
            risk_per_trade_pct: Max risk per trade (default 2%)
            max_daily_risk_pct: Max daily risk (default 5%)
        """
        self.account_size = account_size
        self.max_contracts = max_contracts
        self.risk_per_trade_pct = risk_per_trade_pct
        self.max_daily_risk_pct = max_daily_risk_pct

        # Tracking
        self.current_equity = account_size
        self.daily_pnl = 0
        self.trades_today = 0
        self.consecutive_wins = 0
        self.consecutive_losses = 0

    def update_equity(self, trade_pnl: float):
        """
        Update account equity after trade

        Args:
            trade_pnl: Profit/loss from trade ($)
        """
        self.current_equity += trade_pnl
        self.daily_pnl += trade_pnl
        self.trades_today += 1

        # Track streaks
        if trade_pnl > 0:
            self.consecutive_wins += 1
            self.consecutive_losses = 0
        elif trade_pnl < 0:
            self.consecutive_losses += 1
            self.consecutive_wins = 0

    def reset_daily(self):
        """Reset daily counters (call at start of each day)"""
        self.daily_pnl = 0
        self.trades_today = 0

    def calculate_base_position_size(self,
                                     stop_loss_ticks: int,
                                     tick_value: float = 10.0) -> int:
        """
        Calculate base position size using fixed fractional risk

        Args:
            stop_loss_ticks: Stop loss in ticks
            tick_value: Dollar value per tick ($10 for CL)

        Returns:
            Number of contracts (1-max_contracts)
        """
        # Maximum risk amount per trade
        max_risk_dollars = self.current_equity * self.risk_per_trade_pct

        # Risk per contract
        risk_per_contract = stop_loss_ticks * tick_value

        # Calculate contracts
        contracts = max_risk_dollars / risk_per_contract

        # Round down and cap
        contracts = int(np.floor(contracts))
        contracts = max(1, min(contracts, self.max_contracts))

        return contracts

    def apply_regime_multiplier(self,
                                base_contracts: int,
                                regime: int,
                                regime_probs: np.ndarray,
                                regime_detector) -> int:
        """
        Adjust position size based on market regime

        Args:
            base_contracts: Base position from risk calculation
            regime: Current regime (0-2)
            regime_probs: Probability distribution
            regime_detector: RegimeDetector instance

        Returns:
            Adjusted contract count
        """
        multiplier = regime_detector.get_position_multiplier(regime, regime_probs)

        adjusted = base_contracts * multiplier

        # Round and cap
        adjusted = int(np.round(adjusted))
        adjusted = max(0, min(adjusted, self.max_contracts))

        return adjusted

    def apply_volatility_scaling(self,
                                 base_contracts: int,
                                 current_atr: float,
                                 baseline_atr: float = 1.5) -> int:
        """
        Scale position inversely with volatility

        Higher volatility → smaller position
        Lower volatility → larger position

        Args:
            base_contracts: Current position size
            current_atr: Current ATR (14-period)
            baseline_atr: Normal ATR level (default 1.5 for CL)

        Returns:
            Adjusted contract count
        """
        # Volatility ratio
        vol_ratio = current_atr / baseline_atr

        # Inverse scaling
        # If ATR doubles (vol_ratio=2.0), position halves (0.5x)
        # If ATR halves (vol_ratio=0.5), position doubles (2.0x)
        scaling = 1.0 / vol_ratio

        # Clamp scaling to reasonable range (0.5x to 2.0x)
        scaling = max(0.5, min(2.0, scaling))

        adjusted = base_contracts * scaling

        # Round and cap
        adjusted = int(np.round(adjusted))
        adjusted = max(0, min(adjusted, self.max_contracts))

        return adjusted

    def apply_performance_adjustment(self, base_contracts: int) -> int:
        """
        Adjust for winning/losing streaks

        After consecutive losses: reduce size (protect capital)
        After consecutive wins: slightly increase (ride hot streak)

        Args:
            base_contracts: Current position size

        Returns:
            Adjusted contract count
        """
        # Losing streak protection
        if self.consecutive_losses >= 3:
            # Cut position by 50% after 3+ losses
            multiplier = 0.5
        elif self.consecutive_losses >= 2:
            # Cut by 25% after 2 losses
            multiplier = 0.75
        # Winning streak boost (more conservative)
        elif self.consecutive_wins >= 5:
            # Increase by 25% after 5+ wins
            multiplier = 1.25
        elif self.consecutive_wins >= 3:
            # Increase by 10% after 3+ wins
            multiplier = 1.1
        else:
            multiplier = 1.0

        adjusted = base_contracts * multiplier

        # Round and cap
        adjusted = int(np.round(adjusted))
        adjusted = max(1, min(adjusted, self.max_contracts))

        return adjusted

    def check_daily_risk_limit(self) -> Tuple[bool, str]:
        """
        Check if daily loss limit has been hit

        Returns:
            Tuple of (can_trade, reason)
        """
        max_daily_loss = self.account_size * self.max_daily_risk_pct

        if self.daily_pnl <= -max_daily_loss:
            return False, f"Daily loss limit hit (${self.daily_pnl:.0f} / ${-max_daily_loss:.0f})"

        remaining_risk = max_daily_loss + self.daily_pnl
        return True, f"Daily risk OK (${remaining_risk:.0f} remaining)"

    def get_position_size(self,
                         stop_loss_ticks: int,
                         regime: int = None,
                         regime_probs: np.ndarray = None,
                         regime_detector = None,
                         current_atr: float = None) -> Tuple[int, Dict]:
        """
        Master function: Calculate optimal position size

        Args:
            stop_loss_ticks: Stop loss in ticks
            regime: Current market regime (optional)
            regime_probs: Regime probabilities (optional)
            regime_detector: RegimeDetector instance (optional)
            current_atr: Current ATR value (optional)

        Returns:
            Tuple of (contracts, calculation_breakdown)
        """
        # Check daily risk limit first
        can_trade, risk_msg = self.check_daily_risk_limit()

        if not can_trade:
            return 0, {'reason': 'DAILY_RISK_LIMIT', 'message': risk_msg}

        # Step 1: Base position from risk management
        base_contracts = self.calculate_base_position_size(stop_loss_ticks)

        breakdown = {
            'step_1_base': base_contracts,
            'account_equity': self.current_equity,
            'daily_pnl': self.daily_pnl
        }

        # Step 2: Regime adjustment
        if regime is not None and regime_detector is not None:
            contracts_regime = self.apply_regime_multiplier(
                base_contracts, regime, regime_probs, regime_detector
            )
            breakdown['step_2_regime'] = contracts_regime

            regime_name = regime_detector.REGIME_NAMES[regime]
            breakdown['regime'] = regime_name
            breakdown['regime_confidence'] = regime_probs[regime]
        else:
            contracts_regime = base_contracts
            breakdown['step_2_regime'] = contracts_regime

        # Step 3: Volatility scaling
        if current_atr is not None:
            contracts_vol = self.apply_volatility_scaling(contracts_regime, current_atr)
            breakdown['step_3_volatility'] = contracts_vol
            breakdown['current_atr'] = current_atr
        else:
            contracts_vol = contracts_regime
            breakdown['step_3_volatility'] = contracts_vol

        # Step 4: Performance adjustment
        contracts_final = self.apply_performance_adjustment(contracts_vol)
        breakdown['step_4_performance'] = contracts_final
        breakdown['consecutive_wins'] = self.consecutive_wins
        breakdown['consecutive_losses'] = self.consecutive_losses

        breakdown['final_contracts'] = contracts_final

        return contracts_final, breakdown

    def get_summary(self) -> Dict:
        """
        Get current position sizer state

        Returns:
            Dict with current stats
        """
        return {
            'account_size': self.account_size,
            'current_equity': self.current_equity,
            'total_pnl': self.current_equity - self.account_size,
            'daily_pnl': self.daily_pnl,
            'trades_today': self.trades_today,
            'consecutive_wins': self.consecutive_wins,
            'consecutive_losses': self.consecutive_losses,
            'equity_pct': (self.current_equity / self.account_size - 1) * 100
        }


def test_position_sizer():
    """
    Test position sizing with various scenarios
    """
    print("="*70)
    print("DYNAMIC POSITION SIZER - TEST SCENARIOS")
    print("="*70)

    sizer = DynamicPositionSizer(
        account_size=50000,
        max_contracts=3,
        risk_per_trade_pct=0.02,
        max_daily_risk_pct=0.05
    )

    # Mock regime detector
    class MockRegimeDetector:
        REGIME_LOW_VOL = 0
        REGIME_HIGH_VOL = 1
        REGIME_TRENDING = 2
        REGIME_NAMES = {0: "LOW_VOL", 1: "HIGH_VOL", 2: "TRENDING"}

        def get_position_multiplier(self, regime, probs):
            confidence = probs[regime]
            if regime == 0:
                return 1.5 * (0.5 + 0.5 * confidence)
            elif regime == 1:
                return 0.25 * (0.5 + 0.5 * confidence)
            else:
                return 0.5 * (0.5 + 0.5 * confidence)

    detector = MockRegimeDetector()

    # Scenario 1: Ideal conditions (low vol regime, high confidence)
    print("\n" + "-"*70)
    print("SCENARIO 1: Ideal Trading Conditions")
    print("-"*70)

    regime = 0  # Low vol
    regime_probs = np.array([0.85, 0.10, 0.05])  # 85% confident
    atr = 1.2  # Below average volatility

    contracts, breakdown = sizer.get_position_size(
        stop_loss_ticks=25,
        regime=regime,
        regime_probs=regime_probs,
        regime_detector=detector,
        current_atr=atr
    )

    print(f"Position Size: {contracts} contracts")
    print(f"Breakdown:")
    for key, value in breakdown.items():
        print(f"  {key}: {value}")

    # Scenario 2: High volatility (should reduce size)
    print("\n" + "-"*70)
    print("SCENARIO 2: High Volatility Regime")
    print("-"*70)

    regime = 1  # High vol
    regime_probs = np.array([0.10, 0.80, 0.10])  # 80% confident high vol
    atr = 2.5  # High volatility

    contracts, breakdown = sizer.get_position_size(
        stop_loss_ticks=25,
        regime=regime,
        regime_probs=regime_probs,
        regime_detector=detector,
        current_atr=atr
    )

    print(f"Position Size: {contracts} contracts")
    print(f"Breakdown:")
    for key, value in breakdown.items():
        print(f"  {key}: {value}")

    # Scenario 3: After losing streak
    print("\n" + "-"*70)
    print("SCENARIO 3: After 3 Consecutive Losses")
    print("-"*70)

    # Simulate 3 losses
    sizer.update_equity(-500)
    sizer.update_equity(-500)
    sizer.update_equity(-500)

    regime = 0
    regime_probs = np.array([0.70, 0.20, 0.10])
    atr = 1.5

    contracts, breakdown = sizer.get_position_size(
        stop_loss_ticks=25,
        regime=regime,
        regime_probs=regime_probs,
        regime_detector=detector,
        current_atr=atr
    )

    print(f"Position Size: {contracts} contracts (reduced due to losses)")
    print(f"Breakdown:")
    for key, value in breakdown.items():
        print(f"  {key}: {value}")

    # Scenario 4: After winning streak
    print("\n" + "-"*70)
    print("SCENARIO 4: After 5 Consecutive Wins")
    print("-"*70)

    # Reset and simulate wins
    sizer.consecutive_losses = 0
    sizer.consecutive_wins = 0

    for _ in range(5):
        sizer.update_equity(300)

    contracts, breakdown = sizer.get_position_size(
        stop_loss_ticks=25,
        regime=regime,
        regime_probs=regime_probs,
        regime_detector=detector,
        current_atr=atr
    )

    print(f"Position Size: {contracts} contracts (boosted after wins)")
    print(f"Breakdown:")
    for key, value in breakdown.items():
        print(f"  {key}: {value}")

    # Summary
    print("\n" + "="*70)
    print("POSITION SIZER SUMMARY")
    print("="*70)
    summary = sizer.get_summary()
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    test_position_sizer()
