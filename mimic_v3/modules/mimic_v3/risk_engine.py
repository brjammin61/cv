"""
RiskEngine.py - Institutional Risk Management with Asymptotic Kelly
MIMIC V3.1 HARDENED

Implements:
- R.2.1: Asymptotic Kelly Criterion (accounts for estimation error)
- R.2.2: Dynamic Drawdown Control (DDC) with smooth curves
- V.1: Variance-adjusted position sizing
- Daily/Weekly loss limits with auto-recovery
- Position correlation management
- Exposure caps per market/event
- Persistence integration for crash recovery
"""

import math
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum

if TYPE_CHECKING:
    from .persistence import MimicDB


class RiskState(Enum):
    NORMAL = "NORMAL"
    CAUTIOUS = "CAUTIOUS"      # 10-15% drawdown
    RESTRICTED = "RESTRICTED"  # 15-25% drawdown
    HALTED = "HALTED"          # >25% DD or daily/weekly limit


@dataclass
class Position:
    """Tracks an open position"""
    trade_id: str
    ticker: str
    event_ticker: str
    side: str
    entry_price: float
    size: float
    contracts: int
    shadow_id: str = ""
    strategy_type: str = ""
    win_prob: float = 0.5
    timestamp: datetime = field(default_factory=datetime.utcnow)
    unrealized_pnl: float = 0.0


@dataclass
class TradeRecord:
    """Historical trade record"""
    trade_id: str
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
    HARDENED Risk Management with Asymptotic Kelly.

    Key Features:
    1. Asymptotic Kelly: f* = (p - q/b) / (1 + 1/n)
    2. Variance-adjusted Kelly: Accounts for probability estimate variance
    3. DDC: Smooth drawdown curve with multiple thresholds
    4. Daily/Weekly limits with auto-recovery
    5. Correlation management via event exposure caps
    6. Persistence integration for crash recovery
    """

    def __init__(
        self,
        capital: float = 1000.00,
        max_daily_loss: float = 30.00,       # Reduced from 50 - tighter daily limit
        max_weekly_loss: float = 100.00,     # Reduced from 150
        max_position_pct: float = 0.05,      # Reduced from 0.10 - max 5% per position
        max_event_exposure: float = 0.15,    # Reduced from 0.25 - max 15% per event
        kelly_fraction: float = 0.20,        # Reduced from 0.25 - more conservative
        min_edge_threshold: float = 0.03,    # Increased from 0.02 - require 3% edge
        max_kelly_bet: float = 0.10,         # Reduced from 0.15
        hard_max_position: float = 25.00,    # NEW: Absolute max $25 per trade
        min_whale_trades: int = 3,           # NEW: Whale must have 3+ trades
        extreme_odds_limit: float = 0.05,    # NEW: Reject <5c or >95c
        db: 'MimicDB' = None,
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
        self.max_kelly_bet = max_kelly_bet
        self.hard_max_position = hard_max_position      # NEW
        self.min_whale_trades = min_whale_trades        # NEW
        self.extreme_odds_limit = extreme_odds_limit    # NEW

        self.db = db
        self.logger = logger or logging.getLogger(__name__)

        # State tracking
        self.state = RiskState.NORMAL
        self.positions: Dict[str, Position] = {}
        self.trade_history: List[TradeRecord] = []

        # Daily/Weekly PnL tracking
        self.daily_pnl = 0.0
        self.weekly_pnl = 0.0
        self.daily_trades = 0
        self.last_daily_reset = datetime.utcnow().date()
        self.last_weekly_reset = datetime.utcnow().isocalendar()[1]

        # Event exposure tracking
        self.event_exposure: Dict[str, float] = defaultdict(float)

        # Win/loss streak tracking for adaptive sizing
        self.recent_outcomes: List[bool] = []
        self.streak_window = 10

        # Statistics
        self.stats = {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "total_pnl": 0.0,
            "max_drawdown": 0.0,
            "max_drawdown_pct": 0.0,
            "trades_rejected_risk": 0,
            "current_streak": 0,  # Positive = wins, negative = losses
            "best_trade": 0.0,
            "worst_trade": 0.0,
            "sharpe_estimate": 0.0
        }

        # Try to recover state from persistence
        self._recover_state()

    def _recover_state(self):
        """Recover state from database after restart"""
        if not self.db:
            return

        try:
            # Load capital state
            saved_capital = self.db.load_state("current_capital")
            if saved_capital is not None:
                self.current_capital = float(saved_capital)
                self.logger.info(f"RISK: Recovered capital: ${self.current_capital:.2f}")

            saved_peak = self.db.load_state("peak_capital")
            if saved_peak is not None:
                self.peak_capital = float(saved_peak)

            # Load open positions
            open_positions = self.db.get_open_positions()
            for pos_data in open_positions:
                pos = Position(
                    trade_id=pos_data['trade_id'],
                    ticker=pos_data['ticker'],
                    event_ticker=pos_data.get('event_ticker', ''),
                    side=pos_data['side'],
                    entry_price=pos_data['entry_price'],
                    size=pos_data['size_usd'],
                    contracts=pos_data.get('contracts', 1),
                    shadow_id=pos_data.get('shadow_id', ''),
                    strategy_type=pos_data.get('strategy_type', ''),
                    win_prob=pos_data.get('win_prob', 0.5)
                )
                self.positions[pos.ticker] = pos
                self.event_exposure[pos.event_ticker] += pos.size

            if self.positions:
                self.logger.info(f"RISK: Recovered {len(self.positions)} open positions")

        except Exception as e:
            self.logger.error(f"RISK: State recovery failed: {e}")

    def _save_state(self):
        """Persist critical state to database"""
        if not self.db:
            return

        try:
            self.db.save_state("current_capital", self.current_capital)
            self.db.save_state("peak_capital", self.peak_capital)
            self.db.save_state("daily_pnl", self.daily_pnl)
            self.db.save_state("risk_state", self.state.value)
        except Exception as e:
            self.logger.error(f"RISK: State save failed: {e}")

    def calculate_position_size(
        self,
        win_prob: float,
        payout_ratio: float = 1.0,
        conviction: float = 1.0,
        estimation_samples: int = 50,
        prob_variance: float = 0.0,
        ticker: str = None,
        event_ticker: str = None,
        resolution_hours: float = None
    ) -> Tuple[float, str]:
        """
        Calculate position size using Asymptotic Kelly with variance adjustment.

        Formulas:
        1. Basic Kelly: f = (p*b - q) / b = p - q/b
        2. Asymptotic: f* = f / (1 + 1/n)
        3. Variance-adjusted: f** = f* * (1 - var(p) * sensitivity)
        4. Time-horizon adjusted: for capital efficiency

        Args:
            win_prob: Estimated P(win)
            payout_ratio: Net payout (e.g., 0.9 for 52c binary)
            conviction: Confidence multiplier [0, 1]
            estimation_samples: Observations used to estimate win_prob
            prob_variance: Variance of probability estimate
            ticker: Market ticker
            event_ticker: Event ticker for correlation
            resolution_hours: Hours until market resolves (for capital efficiency)

        Returns:
            (size_dollars, reason_string)
        """
        self._check_period_reset()

        # ========== HALT CHECK ==========
        if self.state == RiskState.HALTED:
            self.stats["trades_rejected_risk"] += 1
            return 0.0, "HALTED: Risk limits reached"

        # ========== INPUT VALIDATION ==========
        if win_prob <= 0 or win_prob >= 1:
            return 0.0, f"Invalid probability: {win_prob}"

        if payout_ratio <= 0:
            return 0.0, f"Invalid payout: {payout_ratio}"

        # ========== EDGE CALCULATION ==========
        q = 1 - win_prob
        edge = win_prob - (q / payout_ratio)

        if edge < self.min_edge_threshold:
            self.stats["trades_rejected_risk"] += 1
            return 0.0, f"Edge too small: {edge:.2%} < {self.min_edge_threshold:.2%}"

        # ========== EXTREME ODDS PROTECTION ==========
        # Reject penny contracts and near-certain markets
        # These have asymmetric risk - small positions = catastrophic losses
        # Infer implied price from payout ratio
        # YES side: payout = (1-p)/p, so p = 1/(1+payout)
        implied_price = 1 / (1 + payout_ratio) if payout_ratio > 0 else 0.5

        if implied_price < self.extreme_odds_limit:
            self.stats["trades_rejected_risk"] += 1
            return 0.0, f"Extreme low odds rejected: {implied_price:.1%} < {self.extreme_odds_limit:.0%} (lottery ticket)"

        if implied_price > (1 - self.extreme_odds_limit):
            self.stats["trades_rejected_risk"] += 1
            return 0.0, f"Extreme high odds rejected: {implied_price:.1%} > {(1-self.extreme_odds_limit):.0%} (near-certain)"

        # ========== WHALE QUALITY FILTER ==========
        # Only follow whales with proven track record
        if estimation_samples < self.min_whale_trades:
            self.stats["trades_rejected_risk"] += 1
            return 0.0, f"Whale unproven: {estimation_samples} trades < {self.min_whale_trades} required"

        # ========== KELLY CALCULATIONS ==========

        # 1. Basic Kelly
        kelly_f = edge / payout_ratio

        # 2. Asymptotic adjustment (accounts for estimation error)
        n = max(estimation_samples, 1)
        asymptotic_factor = 1 / (1 + 1/n)
        asymptotic_kelly = kelly_f * asymptotic_factor

        # 3. Variance adjustment (if variance provided)
        if prob_variance > 0:
            # Sensitivity of Kelly to probability changes
            sensitivity = (1 + 1/payout_ratio) / payout_ratio if payout_ratio > 0 else 1
            variance_adjustment = max(0.1, 1 - prob_variance * sensitivity * 10)
            asymptotic_kelly *= variance_adjustment

        # 4. Apply fractional Kelly
        fractional_kelly = asymptotic_kelly * self.kelly_fraction

        # 5. Cap at maximum bet size
        fractional_kelly = min(fractional_kelly, self.max_kelly_bet)

        # ========== DRAWDOWN CONTROL ==========
        ddc_multiplier = self._calculate_ddc_multiplier()

        # ========== STREAK ADJUSTMENT ==========
        streak_multiplier = self._calculate_streak_multiplier()

        # ========== CONVICTION ==========
        conviction = max(0.0, min(1.0, conviction))

        # ========== TIME-HORIZON WEIGHTING ==========
        # Adjust position size based on capital lockup period
        # Shorter resolution = faster turnover = larger allocation
        # Based on "Time Horizon of Maximum Edge" strategy
        if resolution_hours is not None and resolution_hours > 0:
            days_to_resolution = resolution_hours / 24.0
            if days_to_resolution < 1:
                # Same day - full allocation, fast turnover
                time_multiplier = 1.0
            elif days_to_resolution < 7:
                # 1-7 days - moderate allocation
                time_multiplier = 0.8
            elif days_to_resolution < 30:
                # 1-4 weeks - reduced allocation (like movie trades)
                time_multiplier = 0.5
            else:
                # 30+ days - only take with massive edge
                time_multiplier = 0.25
        else:
            time_multiplier = 1.0  # Default if not provided

        # ========== FINAL SIZE ==========
        base_size = self.current_capital * fractional_kelly
        adjusted_size = base_size * ddc_multiplier * streak_multiplier * conviction * time_multiplier

        # ========== APPLY CAPS ==========

        # Per-position cap
        max_position = self.current_capital * self.max_position_pct
        size = min(adjusted_size, max_position)

        # Event exposure cap
        if event_ticker:
            current_exposure = self.event_exposure.get(event_ticker, 0)
            max_event = self.current_capital * self.max_event_exposure
            available = max(0, max_event - current_exposure)
            if size > available:
                if available <= 0:
                    self.stats["trades_rejected_risk"] += 1
                    return 0.0, f"Event exposure limit: ${current_exposure:.2f}"
                size = available

        # Portfolio exposure cap - CRITICAL: prevent over-deployment
        available_capital = max(0, self.current_capital - self.deployed_capital)
        max_exposure_pct = 0.95  # Max 95% of capital deployed
        max_deployable = self.current_capital * max_exposure_pct - self.deployed_capital

        if max_deployable <= 0:
            self.stats["trades_rejected_risk"] += 1
            return 0.0, f"Max exposure reached: {(self.deployed_capital/self.current_capital)*100:.1f}%"

        if size > available_capital:
            if available_capital < 1.0:
                self.stats["trades_rejected_risk"] += 1
                return 0.0, f"No available capital: ${available_capital:.2f}"
            size = min(size, available_capital, max_deployable)
            self.logger.debug(f"RISK: Capped size to available capital: ${size:.2f}")

        # ========== HARD POSITION CAP ==========
        # Absolute maximum per trade regardless of Kelly
        if size > self.hard_max_position:
            self.logger.debug(f"RISK: Hard cap applied: ${size:.2f} -> ${self.hard_max_position:.2f}")
            size = self.hard_max_position

        # Minimum size threshold
        if size < 1.0:
            self.stats["trades_rejected_risk"] += 1
            return 0.0, f"Size below minimum: ${size:.2f}"

        # Round to cents
        size = round(size, 2)

        self.logger.debug(
            f"RISK SIZE: edge={edge:.2%} kelly={kelly_f:.2%} "
            f"asymp={asymptotic_factor:.2f} frac={fractional_kelly:.2%} "
            f"ddc={ddc_multiplier:.2f} streak={streak_multiplier:.2f} "
            f"conv={conviction:.2f} time={time_multiplier:.2f} -> ${size:.2f}"
        )

        return size, "OK"

    def _calculate_ddc_multiplier(self) -> float:
        """
        Dynamic Drawdown Control with smooth curve.

        TIGHTENED for capital preservation:
        - Halt at 10% (was 25%)
        - Start reducing at 3% (was 10%)
        - More aggressive reduction curve

        Returns multiplier [0, 1] based on current drawdown.
        """
        if self.current_capital >= self.peak_capital:
            self.state = RiskState.NORMAL
            return 1.0

        drawdown = (self.peak_capital - self.current_capital) / self.peak_capital
        self.stats["max_drawdown"] = max(self.stats["max_drawdown"],
                                          self.peak_capital - self.current_capital)
        self.stats["max_drawdown_pct"] = max(self.stats["max_drawdown_pct"], drawdown)

        # HALT at 10% drawdown (was 25%) - protect capital
        if drawdown >= 0.10:
            self.state = RiskState.HALTED
            self.logger.warning(f"RISK HALTED: {drawdown:.1%} drawdown >= 10%")
            return 0.0

        # RESTRICTED: 7-10% drawdown (was 15-25%)
        if drawdown >= 0.07:
            self.state = RiskState.RESTRICTED
            # Smooth curve: 0.3 at 7%, 0.1 at 10%
            mult = 0.3 - (drawdown - 0.07) * 6.67
            return max(0.1, mult)

        # CAUTIOUS: 3-7% drawdown (was 10-15%)
        if drawdown >= 0.03:
            self.state = RiskState.CAUTIOUS
            # Smooth curve: 0.6 at 3%, 0.3 at 7%
            mult = 0.6 - (drawdown - 0.03) * 7.5
            return max(0.3, mult)

        # NORMAL: 0-3% drawdown
        self.state = RiskState.NORMAL
        # Linear reduction: 1.0 at 0%, 0.6 at 3%
        return 1.0 - (drawdown * 13.33)

    def _calculate_streak_multiplier(self) -> float:
        """
        Adjust sizing based on recent win/loss streak.

        Reduces size after losses, maintains after wins.
        """
        if len(self.recent_outcomes) < 3:
            return 1.0

        recent = self.recent_outcomes[-5:]
        wins = sum(1 for x in recent if x)
        losses = len(recent) - wins

        # Losing streak: reduce size
        if losses >= 4:
            return 0.5
        if losses >= 3:
            return 0.7

        # Winning streak: maintain (don't increase to avoid overconfidence)
        return 1.0

    def _check_period_reset(self):
        """Reset daily/weekly counters if needed"""
        now = datetime.utcnow()
        today = now.date()
        this_week = now.isocalendar()[1]

        # Daily reset
        if today != self.last_daily_reset:
            self.logger.info(f"RISK: Daily reset | Yesterday PnL: ${self.daily_pnl:.2f}")
            self.daily_pnl = 0.0
            self.daily_trades = 0
            self.last_daily_reset = today

            # Un-halt if new day and drawdown recovered
            if self.state == RiskState.HALTED:
                dd = (self.peak_capital - self.current_capital) / self.peak_capital
                if dd < 0.20:
                    self.state = RiskState.CAUTIOUS
                    self.logger.info("RISK: Resuming in CAUTIOUS mode")

        # Weekly reset
        if this_week != self.last_weekly_reset:
            self.logger.info(f"RISK: Weekly reset | Week PnL: ${self.weekly_pnl:.2f}")
            self.weekly_pnl = 0.0
            self.last_weekly_reset = this_week

    def open_position(
        self,
        trade_id: str,
        ticker: str,
        event_ticker: str,
        side: str,
        price: float,
        size: float,
        contracts: int,
        shadow_id: str = "",
        strategy_type: str = "",
        win_prob: float = 0.5
    ):
        """Record opening a position"""
        position = Position(
            trade_id=trade_id,
            ticker=ticker,
            event_ticker=event_ticker,
            side=side,
            entry_price=price,
            size=size,
            contracts=contracts,
            shadow_id=shadow_id,
            strategy_type=strategy_type,
            win_prob=win_prob
        )

        self.positions[ticker] = position
        self.event_exposure[event_ticker] += size

        # Persist to database
        if self.db:
            self.db.log_trade_open(
                trade_id=trade_id,
                shadow_id=shadow_id,
                ticker=ticker,
                event_ticker=event_ticker,
                side=side,
                size_usd=size,
                contracts=contracts,
                entry_price=price,
                strategy_type=strategy_type,
                win_prob=win_prob
            )

        self.logger.info(f"RISK: Position opened | {ticker} {side} ${size:.2f} @ {price:.2f}")

    def close_position(self, ticker: str, exit_price: float) -> Optional[float]:
        """
        Close a position and calculate P&L.

        For binary options:
        - YES wins: exit_price = 1.0, pnl = (1 - entry) * contracts
        - YES loses: exit_price = 0.0, pnl = -entry * contracts
        - NO wins: exit_price = 0.0, pnl = (entry) * contracts
        - NO loses: exit_price = 1.0, pnl = -(1-entry) * contracts
        """
        if ticker not in self.positions:
            return None

        position = self.positions[ticker]

        # Calculate P&L for binary options
        if position.side == "yes":
            if exit_price >= 0.5:  # YES won
                pnl = position.size * ((1 - position.entry_price) / position.entry_price)
            else:  # YES lost
                pnl = -position.size
        else:  # NO side
            if exit_price <= 0.5:  # NO won (event didn't happen)
                pnl = position.size * (position.entry_price / (1 - position.entry_price))
            else:  # NO lost
                pnl = -position.size

        is_win = pnl > 0

        # Update equity
        self.update_equity(pnl)

        # Record trade
        record = TradeRecord(
            trade_id=position.trade_id,
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
            self.stats["best_trade"] = max(self.stats["best_trade"], pnl)
        else:
            self.stats["losing_trades"] += 1
            self.stats["worst_trade"] = min(self.stats["worst_trade"], pnl)

        # Track streak
        self.recent_outcomes.append(is_win)
        if len(self.recent_outcomes) > 20:
            self.recent_outcomes = self.recent_outcomes[-20:]

        # Update streak counter
        if is_win:
            if self.stats["current_streak"] >= 0:
                self.stats["current_streak"] += 1
            else:
                self.stats["current_streak"] = 1
        else:
            if self.stats["current_streak"] <= 0:
                self.stats["current_streak"] -= 1
            else:
                self.stats["current_streak"] = -1

        # Persist to database
        if self.db:
            self.db.log_trade_close(position.trade_id, exit_price, pnl)

        # Clean up
        self.event_exposure[position.event_ticker] -= position.size
        del self.positions[ticker]

        self.logger.info(
            f"RISK: Position closed | {ticker} | "
            f"{'WIN' if is_win else 'LOSS'} ${pnl:+.2f} | "
            f"Capital: ${self.current_capital:.2f}"
        )

        return pnl

    def update_equity(self, pnl: float):
        """Update capital and check limits"""
        self.current_capital += pnl
        self.stats["total_pnl"] += pnl

        # Update peak
        if self.current_capital > self.peak_capital:
            self.peak_capital = self.current_capital

        # Update period PnL
        self.daily_pnl += pnl
        self.weekly_pnl += pnl
        self.daily_trades += 1

        # Check daily limit
        if self.daily_pnl <= -self.max_daily_loss:
            self.state = RiskState.HALTED
            self.logger.warning(f"RISK HALTED: Daily loss limit (${self.daily_pnl:.2f})")

        # Check weekly limit
        if self.weekly_pnl <= -self.max_weekly_loss:
            self.state = RiskState.HALTED
            self.logger.warning(f"RISK HALTED: Weekly loss limit (${self.weekly_pnl:.2f})")

        # Persist state
        self._save_state()

    def can_trade(self) -> Tuple[bool, str]:
        """Check if trading is allowed"""
        self._check_period_reset()

        if self.state == RiskState.HALTED:
            return False, f"Trading halted (DD: {self._get_drawdown_pct():.1%})"

        return True, "OK"

    def _get_drawdown_pct(self) -> float:
        """Get current drawdown percentage"""
        if self.peak_capital <= 0:
            return 0.0
        return (self.peak_capital - self.current_capital) / self.peak_capital

    @property
    def deployed_capital(self) -> float:
        """Total capital currently deployed in open positions"""
        return sum(p.size for p in self.positions.values())

    @property
    def open_positions(self) -> Dict[str, Position]:
        """Alias for positions dict - used by dashboard API"""
        return self.positions

    @property
    def realized_pnl_today(self) -> float:
        """Alias for daily_pnl - used by dashboard API"""
        return self.daily_pnl

    @property
    def win_rate(self) -> float:
        """Win rate as percentage - used by dashboard API"""
        return self._get_recent_win_rate() * 100

    @property
    def trades_today(self) -> int:
        """Alias for daily_trades - used by dashboard API"""
        return self.daily_trades

    @property
    def current_drawdown(self) -> float:
        """Current drawdown as decimal - used by dashboard API"""
        return self._get_drawdown_pct()

    @property
    def max_drawdown(self) -> float:
        """Max drawdown as decimal - used by dashboard API"""
        return self.stats.get("max_drawdown_pct", 0.0)

    @property
    def max_portfolio_exposure(self) -> float:
        """Max allowed exposure as decimal - used by dashboard API"""
        return self.max_event_exposure

    @property
    def ddc_multiplier(self) -> float:
        """Current DDC multiplier - used by dashboard API"""
        return self._calculate_ddc_multiplier()

    @property
    def ddc_status(self) -> str:
        """Current DDC status string - used by dashboard API"""
        return self.state.value

    @property
    def win_streak(self) -> int:
        """Current win streak - used by dashboard API"""
        streak = self.stats.get("current_streak", 0)
        return streak if streak > 0 else 0

    @property
    def loss_streak(self) -> int:
        """Current loss streak - used by dashboard API"""
        streak = self.stats.get("current_streak", 0)
        return abs(streak) if streak < 0 else 0

    def get_status(self) -> Dict:
        """Get comprehensive risk status"""
        return {
            "state": self.state.value,
            "capital": round(self.current_capital, 2),
            "initial_capital": round(self.initial_capital, 2),
            "peak_capital": round(self.peak_capital, 2),
            "drawdown_pct": round(self._get_drawdown_pct() * 100, 2),
            "daily_pnl": round(self.daily_pnl, 2),
            "weekly_pnl": round(self.weekly_pnl, 2),
            "daily_trades": self.daily_trades,
            "open_positions": len(self.positions),
            "total_exposure": sum(p.size for p in self.positions.values()),
            "event_exposures": dict(self.event_exposure),
            "stats": self.stats,
            "recent_win_rate": self._get_recent_win_rate()
        }

    def _get_recent_win_rate(self) -> float:
        """Get win rate from recent outcomes"""
        if not self.recent_outcomes:
            return 0.5
        return sum(1 for x in self.recent_outcomes if x) / len(self.recent_outcomes)

    def get_position_summary(self) -> List[Dict]:
        """Get summary of open positions"""
        return [
            {
                "trade_id": p.trade_id,
                "ticker": p.ticker,
                "event": p.event_ticker,
                "side": p.side,
                "size": p.size,
                "entry": p.entry_price,
                "shadow_id": p.shadow_id,
                "strategy": p.strategy_type,
                "win_prob": p.win_prob
            }
            for p in self.positions.values()
        ]

    def force_reset(self):
        """Force reset risk state (use with caution)"""
        self.state = RiskState.NORMAL
        self.daily_pnl = 0.0
        self.weekly_pnl = 0.0
        self.recent_outcomes.clear()
        self.stats["current_streak"] = 0
        self.logger.warning("RISK: Forced reset")
        self._save_state()


# ==================== KELLY UTILITIES ====================

def kelly_simple(p: float, b: float) -> float:
    """Basic Kelly: f* = (p*b - q) / b"""
    q = 1 - p
    return (p * b - q) / b if b > 0 else 0


def kelly_asymptotic(p: float, b: float, n: int) -> float:
    """Asymptotic Kelly with sample adjustment"""
    base = kelly_simple(p, b)
    if base <= 0:
        return 0
    return base / (1 + 1/max(n, 1))


def kelly_variance_adjusted(p: float, b: float, p_var: float) -> float:
    """Kelly adjusted for probability variance"""
    base = kelly_simple(p, b)
    if base <= 0:
        return 0
    sensitivity = (1 + 1/b) / b if b > 0 else 1
    adjustment = max(0, 1 - p_var * sensitivity * 10)
    return base * adjustment
