"""
RiskEngine.py - Institutional Risk Management with Asymptotic Kelly
MIMIC V3.1 - Production Ready

Implements:
- Asymptotic Kelly Criterion (accounts for estimation error)
- Dynamic Drawdown Control (DDC)
- Daily/Weekly loss limits
- Position correlation management
- Exposure caps per market/event
"""

import math
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum


class RiskState(Enum):
    NORMAL = "NORMAL"
    CAUTIOUS = "CAUTIOUS"   # Light drawdown
    RESTRICTED = "RESTRICTED"  # Heavy drawdown
    HALTED = "HALTED"  # Stop loss hit


@dataclass
class Position:
    """Tracks an open position"""
    ticker: str
    event_ticker: str
    side: str
    entry_price: float
    size: float  # Dollar amount
    contracts: int
    timestamp: datetime = field(default_factory=datetime.utcnow)
    unrealized_pnl: float = 0.0


@dataclass
class TradeRecord:
    """Historical trade record"""
    ticker: str
    side: str
    size: float
    entry_price: float
    exit_price: float
    pnl: float
    timestamp: datetime
    is_win: bool


class InstitutionalRiskManager:
    """
    Advanced risk management with Asymptotic Kelly sizing.

    Key Features:
    1. Asymptotic Kelly: Adjusts for estimation uncertainty
    2. DDC: Reduces size as drawdown increases
    3. Daily/Weekly limits: Hard stops on cumulative losses
    4. Correlation management: Limits exposure to related events
    5. Per-market caps: Maximum position per ticker
    """

    def __init__(
        self,
        capital: float = 1000.00,
        max_daily_loss: float = 50.00,
        max_weekly_loss: float = 150.00,
        max_position_pct: float = 0.10,  # 10% of capital per position
        max_event_exposure: float = 0.25,  # 25% of capital per event
        kelly_fraction: float = 0.25,  # Quarter Kelly default
        min_edge_threshold: float = 0.02,  # 2% minimum edge to trade
        logger: logging.Logger = None
    ):
        self.initial_capital = capital
        self.current_capital = capital
        self.peak_capital = capital

        self.max_daily_loss = max_daily_loss
        self.max_weekly_loss = max_weekly_loss
        self.max_position_pct = max_position_pct
        self.max_event_exposure = max_event_exposure
        self.kelly_fraction = kelly_fraction
        self.min_edge_threshold = min_edge_threshold

        self.logger = logger or logging.getLogger(__name__)

        # State tracking
        self.state = RiskState.NORMAL
        self.positions: Dict[str, Position] = {}
        self.trade_history: List[TradeRecord] = []

        # Daily/Weekly PnL tracking
        self.daily_pnl = 0.0
        self.weekly_pnl = 0.0
        self.last_daily_reset = datetime.utcnow().date()
        self.last_weekly_reset = datetime.utcnow().isocalendar()[1]

        # Event exposure tracking
        self.event_exposure: Dict[str, float] = defaultdict(float)

        # Statistics
        self.stats = {
            "total_trades": 0,
            "winning_trades": 0,
            "total_pnl": 0.0,
            "max_drawdown": 0.0,
            "trades_rejected_risk": 0
        }

    def calculate_position_size(
        self,
        win_prob: float,
        payout_ratio: float = 1.0,
        conviction: float = 1.0,
        estimation_samples: int = 50,
        ticker: str = None,
        event_ticker: str = None
    ) -> Tuple[float, str]:
        """
        Calculate position size using Asymptotic Kelly Criterion.

        The Asymptotic Kelly formula accounts for estimation error:
        f* = (p - q/b) / (1 + 1/n)

        Where:
        - p = probability of win
        - q = 1 - p (probability of loss)
        - b = payout ratio (net odds)
        - n = number of samples used to estimate p

        Args:
            win_prob: Estimated probability of winning (0-1)
            payout_ratio: Net payout on win (e.g., 0.9 for binary at 0.52)
            conviction: Confidence multiplier (0-1)
            estimation_samples: Number of observations used to estimate win_prob
            ticker: Market ticker for position limits
            event_ticker: Event ticker for correlation limits

        Returns:
            (size, reason): Dollar size and explanation
        """
        # Reset daily/weekly if needed
        self._check_period_reset()

        # Check halt conditions
        if self.state == RiskState.HALTED:
            return 0.0, "HALTED: Daily/Weekly loss limit reached"

        # Basic validation
        if win_prob <= 0 or win_prob >= 1:
            return 0.0, f"Invalid probability: {win_prob}"

        if payout_ratio <= 0:
            return 0.0, f"Invalid payout ratio: {payout_ratio}"

        # Calculate edge
        q = 1 - win_prob
        edge = win_prob - (q / payout_ratio)

        if edge < self.min_edge_threshold:
            return 0.0, f"Edge too small: {edge:.2%} < {self.min_edge_threshold:.2%}"

        # ========== ASYMPTOTIC KELLY ==========
        # Standard Kelly
        kelly_f = edge / payout_ratio

        # Asymptotic adjustment for estimation uncertainty
        # As n -> inf, this approaches standard Kelly
        # With small n, it reduces position size significantly
        asymptotic_factor = 1 / (1 + 1 / max(estimation_samples, 1))
        adjusted_kelly = kelly_f * asymptotic_factor

        # Apply fractional Kelly
        fractional_kelly = adjusted_kelly * self.kelly_fraction

        # ========== DRAWDOWN CONTROL ==========
        ddc_multiplier = self._calculate_ddc_multiplier()

        # ========== CONVICTION ADJUSTMENT ==========
        conviction = max(0.0, min(1.0, conviction))

        # ========== FINAL SIZE CALCULATION ==========
        raw_size = self.current_capital * fractional_kelly * ddc_multiplier * conviction

        # ========== APPLY CAPS ==========
        # Per-position cap
        max_position = self.current_capital * self.max_position_pct
        size = min(raw_size, max_position)

        # Event exposure cap
        if event_ticker:
            current_event_exposure = self.event_exposure.get(event_ticker, 0)
            max_event = self.current_capital * self.max_event_exposure
            available_event = max(0, max_event - current_event_exposure)
            if size > available_event:
                size = available_event
                if size <= 0:
                    return 0.0, f"Event exposure limit reached: ${current_event_exposure:.2f}"

        # Minimum size threshold
        if size < 1.0:
            return 0.0, f"Size below minimum: ${size:.2f}"

        # Round to nearest dollar
        size = round(size, 2)

        # Log sizing breakdown
        self.logger.debug(
            f"Size calc: edge={edge:.2%}, kelly={kelly_f:.2%}, "
            f"asymp={asymptotic_factor:.2f}, frac={fractional_kelly:.2%}, "
            f"ddc={ddc_multiplier:.2f}, conv={conviction:.2f}, "
            f"raw=${raw_size:.2f}, final=${size:.2f}"
        )

        return size, "OK"

    def _calculate_ddc_multiplier(self) -> float:
        """
        Dynamic Drawdown Control multiplier.

        Reduces position size as drawdown increases:
        - 0% DD: 1.0x (full size)
        - 10% DD: 0.8x
        - 20% DD: 0.5x
        - 30%+ DD: HALT
        """
        if self.current_capital >= self.peak_capital:
            self.state = RiskState.NORMAL
            return 1.0

        drawdown = (self.peak_capital - self.current_capital) / self.peak_capital
        self.stats["max_drawdown"] = max(self.stats["max_drawdown"], drawdown)

        if drawdown >= 0.30:
            self.state = RiskState.HALTED
            self.logger.warning(f"HALTED: 30% drawdown reached ({drawdown:.1%})")
            return 0.0

        if drawdown >= 0.20:
            self.state = RiskState.RESTRICTED
            return 0.5

        if drawdown >= 0.10:
            self.state = RiskState.CAUTIOUS
            return max(0.5, 1.0 - (drawdown * 2))

        self.state = RiskState.NORMAL
        return 1.0 - drawdown

    def _check_period_reset(self):
        """Reset daily/weekly PnL counters if needed"""
        now = datetime.utcnow()
        today = now.date()
        this_week = now.isocalendar()[1]

        # Daily reset
        if today != self.last_daily_reset:
            self.daily_pnl = 0.0
            self.last_daily_reset = today

            # Un-halt if new day and not in deep drawdown
            if self.state == RiskState.HALTED:
                dd = (self.peak_capital - self.current_capital) / self.peak_capital
                if dd < 0.30:
                    self.state = RiskState.NORMAL
                    self.logger.info("Risk state reset to NORMAL (new day)")

        # Weekly reset
        if this_week != self.last_weekly_reset:
            self.weekly_pnl = 0.0
            self.last_weekly_reset = this_week

    def open_position(
        self,
        ticker: str,
        event_ticker: str,
        side: str,
        price: float,
        size: float,
        contracts: int
    ):
        """Record opening a position"""
        position = Position(
            ticker=ticker,
            event_ticker=event_ticker,
            side=side,
            entry_price=price,
            size=size,
            contracts=contracts
        )
        self.positions[ticker] = position
        self.event_exposure[event_ticker] += size
        self.logger.info(f"Opened position: {ticker} {side} ${size:.2f} @ {price:.2f}")

    def close_position(self, ticker: str, exit_price: float) -> Optional[float]:
        """
        Close a position and record P&L.

        Returns:
            P&L amount or None if no position
        """
        if ticker not in self.positions:
            return None

        position = self.positions[ticker]

        # Calculate P&L
        if position.side == "yes":
            # YES: win if settles at 1, lose if settles at 0
            pnl = position.size * (exit_price - position.entry_price) / position.entry_price
        else:
            # NO: inverse
            pnl = position.size * (position.entry_price - exit_price) / (1 - position.entry_price)

        is_win = pnl > 0

        # Update equity
        self.update_equity(pnl)

        # Record trade
        record = TradeRecord(
            ticker=ticker,
            side=position.side,
            size=position.size,
            entry_price=position.entry_price,
            exit_price=exit_price,
            pnl=pnl,
            timestamp=datetime.utcnow(),
            is_win=is_win
        )
        self.trade_history.append(record)

        # Update stats
        self.stats["total_trades"] += 1
        if is_win:
            self.stats["winning_trades"] += 1

        # Clean up
        self.event_exposure[position.event_ticker] -= position.size
        del self.positions[ticker]

        self.logger.info(
            f"Closed position: {ticker} | "
            f"{'WIN' if is_win else 'LOSS'} ${pnl:.2f} | "
            f"Capital: ${self.current_capital:.2f}"
        )

        return pnl

    def update_equity(self, pnl: float):
        """
        Update capital and check limits.

        Args:
            pnl: Profit/loss amount
        """
        self.current_capital += pnl
        self.stats["total_pnl"] += pnl

        # Update peak
        if self.current_capital > self.peak_capital:
            self.peak_capital = self.current_capital

        # Update period PnL
        self.daily_pnl += pnl
        self.weekly_pnl += pnl

        # Check limits
        if self.daily_pnl <= -self.max_daily_loss:
            self.state = RiskState.HALTED
            self.logger.warning(f"HALTED: Daily loss limit (${self.daily_pnl:.2f})")

        if self.weekly_pnl <= -self.max_weekly_loss:
            self.state = RiskState.HALTED
            self.logger.warning(f"HALTED: Weekly loss limit (${self.weekly_pnl:.2f})")

    def can_trade(self) -> Tuple[bool, str]:
        """Check if trading is allowed"""
        self._check_period_reset()

        if self.state == RiskState.HALTED:
            return False, "Trading halted due to loss limits"

        return True, "OK"

    def get_status(self) -> Dict:
        """Get current risk status"""
        drawdown = (self.peak_capital - self.current_capital) / self.peak_capital if self.peak_capital > 0 else 0

        return {
            "state": self.state.value,
            "capital": round(self.current_capital, 2),
            "peak_capital": round(self.peak_capital, 2),
            "drawdown": round(drawdown * 100, 2),
            "daily_pnl": round(self.daily_pnl, 2),
            "weekly_pnl": round(self.weekly_pnl, 2),
            "open_positions": len(self.positions),
            "total_exposure": sum(p.size for p in self.positions.values()),
            "stats": self.stats
        }

    def get_position_summary(self) -> List[Dict]:
        """Get summary of all open positions"""
        return [
            {
                "ticker": p.ticker,
                "event": p.event_ticker,
                "side": p.side,
                "size": p.size,
                "entry": p.entry_price,
                "unrealized_pnl": p.unrealized_pnl
            }
            for p in self.positions.values()
        ]

    def reset_day(self):
        """Manual daily reset"""
        self.daily_pnl = 0.0
        self.last_daily_reset = datetime.utcnow().date()
        if self.state == RiskState.HALTED:
            dd = (self.peak_capital - self.current_capital) / self.peak_capital
            if dd < 0.30:
                self.state = RiskState.NORMAL
        self.logger.info("Daily risk counters reset")


# ==================== KELLY CALCULATOR UTILITIES ====================

def calculate_kelly_simple(p: float, b: float) -> float:
    """
    Simple Kelly formula: f* = (p*b - q) / b

    Args:
        p: Win probability
        b: Payout ratio (net odds)

    Returns:
        Optimal fraction of bankroll
    """
    q = 1 - p
    return (p * b - q) / b if b > 0 else 0


def calculate_kelly_asymptotic(p: float, b: float, n: int) -> float:
    """
    Asymptotic Kelly with sample size adjustment.

    Args:
        p: Estimated win probability
        b: Payout ratio
        n: Number of samples

    Returns:
        Adjusted optimal fraction
    """
    base_kelly = calculate_kelly_simple(p, b)
    if base_kelly <= 0:
        return 0
    return base_kelly / (1 + 1/max(n, 1))


def calculate_kelly_with_variance(
    p: float,
    b: float,
    p_variance: float
) -> float:
    """
    Kelly adjusted for probability estimation variance.

    Uses the formula: f* = f_kelly * (1 - var(p) * sensitivity)

    Args:
        p: Estimated win probability
        b: Payout ratio
        p_variance: Variance of probability estimate

    Returns:
        Variance-adjusted optimal fraction
    """
    base_kelly = calculate_kelly_simple(p, b)
    if base_kelly <= 0:
        return 0

    # Sensitivity of Kelly to p changes
    # df/dp = (1 + 1/b) / b
    sensitivity = (1 + 1/b) / b if b > 0 else 1

    # Reduce Kelly based on estimation uncertainty
    adjustment = max(0, 1 - p_variance * sensitivity * 10)
    return base_kelly * adjustment
