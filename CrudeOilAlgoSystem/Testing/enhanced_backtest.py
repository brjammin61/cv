"""
Enhanced Backtesting Framework with Quality Filters
====================================================

Extends the comprehensive backtest with three quality filters:
1. Multi-timeframe trend filter (1H EMA)
2. Volatility regime filter (ATR-based)
3. Time-of-day session filter

These filters improve win rate and profit factor by avoiding low-quality setups.

Author: Algorithmic Trading Framework 2025
"""

import numpy as np
import pandas as pd
from datetime import datetime, time
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Testing.comprehensive_backtest import BacktestEngine, run_parameter_grid_search
from itertools import product


class EnhancedBacktestEngine(BacktestEngine):
    """
    Extended backtest engine with quality filters
    """

    def __init__(self, data: pd.DataFrame, initial_balance=50000):
        """
        Initialize enhanced backtest engine

        Args:
            data: Historical OHLCV data with timestamp
            initial_balance: Starting capital
        """
        super().__init__(data, initial_balance)

        # Prepare data for filters
        self._prepare_data()

    def _prepare_data(self):
        """
        Prepare data with timestamps for time-based filters
        """
        # Ensure timestamp is datetime
        if 'timestamp' in self.data.columns:
            self.data['timestamp'] = pd.to_datetime(self.data['timestamp'])
            self.data['hour'] = self.data['timestamp'].dt.hour
            self.data['minute'] = self.data['timestamp'].dt.minute
        else:
            # Create dummy timestamps if not available
            self.data['hour'] = 10  # Default to trading hours
            self.data['minute'] = 0

    def _calculate_hourly_ema(self, period=50):
        """
        Calculate 1-hour EMA from 1-minute bars

        For 1-minute data, we resample to hourly and calculate EMA,
        then forward-fill to match original data length.

        Args:
            period: EMA period (default 50)

        Returns:
            Series with EMA values for each bar
        """
        if 'timestamp' not in self.data.columns:
            # No timestamp data, return neutral signal
            return pd.Series([1] * len(self.data))

        # Resample to hourly
        hourly = self.data.set_index('timestamp').resample('1H')['close'].last()

        # Calculate EMA on hourly data
        hourly_ema = hourly.ewm(span=period, adjust=False).mean()

        # Calculate slope (rising/falling)
        hourly_slope = hourly_ema.diff()

        # Map back to original timeframe
        self.data.set_index('timestamp', inplace=True)
        slope_mapped = hourly_slope.reindex(self.data.index, method='ffill')
        self.data.reset_index(inplace=True)

        return slope_mapped

    def _calculate_atr(self, bars, period=14):
        """
        Calculate Average True Range for volatility filter

        Args:
            bars: Recent bars DataFrame
            period: ATR period

        Returns:
            ATR value
        """
        if len(bars) < period + 1:
            return 1.0  # Default neutral value

        high = bars['high'].values
        low = bars['low'].values
        close = bars['close'].values

        # True Range calculation
        tr = np.maximum(
            high[1:] - low[1:],  # High - Low
            np.maximum(
                np.abs(high[1:] - close[:-1]),  # High - Previous Close
                np.abs(low[1:] - close[:-1])    # Low - Previous Close
            )
        )

        # ATR is EMA of True Range
        atr = pd.Series(tr).ewm(span=period, adjust=False).mean().iloc[-1]

        return atr

    def _is_trading_session(self, hour, minute):
        """
        Check if current time is in active trading session

        High-liquidity sessions for crude oil:
        - 9:00-11:30 AM EST (morning session)
        - 1:30-2:30 PM EST (afternoon session)

        Args:
            hour: Hour of day (0-23)
            minute: Minute of hour (0-59)

        Returns:
            True if in trading session
        """
        # Convert to time object
        current_time = time(hour, minute)

        # Morning session: 9:00-11:30
        morning_start = time(9, 0)
        morning_end = time(11, 30)

        # Afternoon session: 13:30-14:30
        afternoon_start = time(13, 30)
        afternoon_end = time(14, 30)

        in_morning = morning_start <= current_time <= morning_end
        in_afternoon = afternoon_start <= current_time <= afternoon_end

        return in_morning or in_afternoon

    def run_vwap_strategy_enhanced(self, params, enable_filters=True):
        """
        Run VWAP strategy with quality filters

        Args:
            params: Strategy parameters
            enable_filters: Dict of filter flags or True to enable all

        Returns:
            Performance metrics dict
        """
        vwap_period = params.get('vwap_period', 20)
        stddev_mult = params.get('stddev_mult', 2.0)
        stop_loss_ticks = params.get('stop_loss_ticks', 25)
        target_ticks = params.get('target_ticks', 20)

        # REALISTIC COSTS
        slippage_ticks = params.get('slippage_ticks', 5)
        spread_ticks = params.get('spread_ticks', 1)
        commission = params.get('commission', 4.12)

        # Filter configuration
        if enable_filters is True:
            enable_filters = {
                'trend': True,
                'volatility': True,
                'session': True
            }
        elif enable_filters is False:
            enable_filters = {
                'trend': False,
                'volatility': False,
                'session': False
            }

        # Volatility filter parameters
        min_atr = params.get('min_atr', 0.8)
        max_atr = params.get('max_atr', 2.0)
        atr_period = params.get('atr_period', 14)

        # Trend filter
        ema_period = params.get('ema_period', 50)

        # Calculate 1H EMA slope if trend filter enabled
        if enable_filters.get('trend', False):
            hourly_slope = self._calculate_hourly_ema(ema_period)
        else:
            hourly_slope = pd.Series([1] * len(self.data))  # Neutral

        balance = self.initial_balance
        position = 0
        entry_price = 0
        trades = []
        equity_curve = []
        filter_blocks = {'trend': 0, 'volatility': 0, 'session': 0}

        max_balance = balance
        max_drawdown = 0

        for i in range(max(vwap_period, atr_period + 1), len(self.data)):
            current_bar = self.data.iloc[i]
            close = current_bar['close']
            hour = current_bar['hour']
            minute = current_bar['minute']

            # Calculate VWAP and bands
            recent_data = self.data.iloc[i-vwap_period:i]
            vwap = (recent_data['close'] * recent_data['volume']).sum() / recent_data['volume'].sum()
            std = recent_data['close'].std()

            upper_band = vwap + (std * stddev_mult)
            lower_band = vwap - (std * stddev_mult)

            # === QUALITY FILTERS ===

            # 1. TREND FILTER: Only trade with 1H trend
            if enable_filters.get('trend', False):
                trend_up = hourly_slope.iloc[i] > 0
                trend_down = hourly_slope.iloc[i] < 0
            else:
                trend_up = True
                trend_down = True

            # 2. VOLATILITY FILTER: Only trade in reasonable volatility regime
            if enable_filters.get('volatility', False):
                atr = self._calculate_atr(self.data.iloc[i-atr_period-1:i], atr_period)
                volatility_ok = min_atr <= atr <= max_atr
            else:
                volatility_ok = True

            # 3. SESSION FILTER: Only trade during high-liquidity sessions
            if enable_filters.get('session', False):
                session_ok = self._is_trading_session(hour, minute)
            else:
                session_ok = True

            # Entry logic with filters
            if position == 0:
                # Long at lower band - requires uptrend
                if close <= lower_band and trend_up and volatility_ok and session_ok:
                    position = 1
                    entry_price = close
                # Short at upper band - requires downtrend
                elif close >= upper_band and trend_down and volatility_ok and session_ok:
                    position = -1
                    entry_price = close
                else:
                    # Track why we didn't enter
                    if close <= lower_band and not trend_up:
                        filter_blocks['trend'] += 1
                    elif close >= upper_band and not trend_down:
                        filter_blocks['trend'] += 1
                    elif not volatility_ok:
                        filter_blocks['volatility'] += 1
                    elif not session_ok:
                        filter_blocks['session'] += 1

            # Exit logic (same as before)
            elif position != 0:
                pnl = 0

                # Check stop loss
                if position == 1 and close <= entry_price - (stop_loss_ticks * 0.01):
                    pnl = (close - entry_price) * 1000
                    position = 0
                elif position == -1 and close >= entry_price + (stop_loss_ticks * 0.01):
                    pnl = (entry_price - close) * 1000
                    position = 0

                # Check profit target
                elif position == 1 and close >= entry_price + (target_ticks * 0.01):
                    pnl = (close - entry_price) * 1000
                    position = 0
                elif position == -1 and close <= entry_price - (target_ticks * 0.01):
                    pnl = (entry_price - close) * 1000
                    position = 0

                # Check VWAP reversion
                elif position == 1 and close >= vwap:
                    pnl = (close - entry_price) * 1000
                    position = 0
                elif position == -1 and close <= vwap:
                    pnl = (entry_price - close) * 1000
                    position = 0

                if pnl != 0:
                    # APPLY REALISTIC COSTS
                    slippage_cost = (slippage_ticks * 2) * 10
                    spread_cost = (spread_ticks * 2) * 10
                    total_cost = slippage_cost + spread_cost + commission

                    pnl -= total_cost

                    balance += pnl
                    trades.append({
                        'entry': entry_price,
                        'exit': close,
                        'pnl': pnl,
                        'gross_pnl': pnl + total_cost,
                        'costs': total_cost,
                        'balance': balance
                    })

            # Track equity
            unrealized_pnl = 0
            if position != 0:
                unrealized_pnl = (close - entry_price) * position * 1000

            current_equity = balance + unrealized_pnl
            equity_curve.append(current_equity)

            # Track drawdown
            if current_equity > max_balance:
                max_balance = current_equity
            current_dd = max_balance - current_equity
            if current_dd > max_drawdown:
                max_drawdown = current_dd

        # Calculate metrics
        if len(trades) == 0:
            metrics = self._empty_metrics()
            metrics['filter_blocks'] = filter_blocks
            return metrics

        trades_df = pd.DataFrame(trades)
        winning_trades = trades_df[trades_df['pnl'] > 0]
        losing_trades = trades_df[trades_df['pnl'] < 0]

        metrics = {
            'total_trades': len(trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': len(winning_trades) / len(trades) if len(trades) > 0 else 0,
            'total_pnl': trades_df['pnl'].sum(),
            'avg_win': winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0,
            'avg_loss': losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0,
            'largest_win': winning_trades['pnl'].max() if len(winning_trades) > 0 else 0,
            'largest_loss': losing_trades['pnl'].min() if len(losing_trades) > 0 else 0,
            'profit_factor': winning_trades['pnl'].sum() / abs(losing_trades['pnl'].sum()) if len(losing_trades) > 0 else 0,
            'max_drawdown': max_drawdown,
            'final_balance': balance,
            'return_pct': ((balance - self.initial_balance) / self.initial_balance) * 100,
            'sharpe_ratio': self._calculate_sharpe(equity_curve),
            'params': params,
            'filter_blocks': filter_blocks,
            'filters_enabled': enable_filters
        }

        return metrics


def run_comparison_test(data: pd.DataFrame, output_dir='./results_enhanced'):
    """
    Run comparison between baseline and enhanced strategies

    Args:
        data: Historical data
        output_dir: Output directory

    Returns:
        Dict with comparison results
    """
    print("="*70)
    print("ENHANCED BACKTEST: BASELINE VS FILTERED COMPARISON")
    print("="*70)

    # Best parameters from previous optimization
    best_params = {
        'vwap_period': 25,
        'stddev_mult': 2.0,
        'stop_loss_ticks': 25,
        'target_ticks': 15,
        'slippage_ticks': 5,
        'spread_ticks': 1,
        'commission': 4.12
    }

    print("\nUsing validated best parameters:")
    for k, v in best_params.items():
        print(f"  {k}: {v}")

    # Initialize engine
    engine = EnhancedBacktestEngine(data)

    # Test 1: Baseline (no filters)
    print("\n" + "-"*70)
    print("TEST 1: BASELINE (No Filters)")
    print("-"*70)
    baseline_metrics = engine.run_vwap_strategy_enhanced(best_params, enable_filters=False)

    print(f"Total Trades: {baseline_metrics['total_trades']}")
    print(f"Win Rate: {baseline_metrics['win_rate']:.2%}")
    print(f"Profit Factor: {baseline_metrics['profit_factor']:.4f}")
    print(f"Total PnL: ${baseline_metrics['total_pnl']:.2f}")
    print(f"Sharpe Ratio: {baseline_metrics['sharpe_ratio']:.4f}")

    # Test 2: Trend filter only
    print("\n" + "-"*70)
    print("TEST 2: TREND FILTER ONLY (1H EMA)")
    print("-"*70)
    trend_metrics = engine.run_vwap_strategy_enhanced(
        best_params,
        enable_filters={'trend': True, 'volatility': False, 'session': False}
    )

    print(f"Total Trades: {trend_metrics['total_trades']}")
    print(f"Win Rate: {trend_metrics['win_rate']:.2%}")
    print(f"Profit Factor: {trend_metrics['profit_factor']:.4f}")
    print(f"Total PnL: ${trend_metrics['total_pnl']:.2f}")
    print(f"Sharpe Ratio: {trend_metrics['sharpe_ratio']:.4f}")
    print(f"Trades Blocked by Trend: {trend_metrics['filter_blocks']['trend']}")

    # Test 3: Volatility filter only
    print("\n" + "-"*70)
    print("TEST 3: VOLATILITY FILTER ONLY (ATR)")
    print("-"*70)
    vol_metrics = engine.run_vwap_strategy_enhanced(
        best_params,
        enable_filters={'trend': False, 'volatility': True, 'session': False}
    )

    print(f"Total Trades: {vol_metrics['total_trades']}")
    print(f"Win Rate: {vol_metrics['win_rate']:.2%}")
    print(f"Profit Factor: {vol_metrics['profit_factor']:.4f}")
    print(f"Total PnL: ${vol_metrics['total_pnl']:.2f}")
    print(f"Sharpe Ratio: {vol_metrics['sharpe_ratio']:.4f}")
    print(f"Trades Blocked by Volatility: {vol_metrics['filter_blocks']['volatility']}")

    # Test 4: Session filter only
    print("\n" + "-"*70)
    print("TEST 4: SESSION FILTER ONLY (Time-of-Day)")
    print("-"*70)
    session_metrics = engine.run_vwap_strategy_enhanced(
        best_params,
        enable_filters={'trend': False, 'volatility': False, 'session': True}
    )

    print(f"Total Trades: {session_metrics['total_trades']}")
    print(f"Win Rate: {session_metrics['win_rate']:.2%}")
    print(f"Profit Factor: {session_metrics['profit_factor']:.4f}")
    print(f"Total PnL: ${session_metrics['total_pnl']:.2f}")
    print(f"Sharpe Ratio: {session_metrics['sharpe_ratio']:.4f}")
    print(f"Trades Blocked by Session: {session_metrics['filter_blocks']['session']}")

    # Test 5: All filters combined
    print("\n" + "-"*70)
    print("TEST 5: ALL FILTERS COMBINED")
    print("-"*70)
    enhanced_metrics = engine.run_vwap_strategy_enhanced(best_params, enable_filters=True)

    print(f"Total Trades: {enhanced_metrics['total_trades']}")
    print(f"Win Rate: {enhanced_metrics['win_rate']:.2%}")
    print(f"Profit Factor: {enhanced_metrics['profit_factor']:.4f}")
    print(f"Total PnL: ${enhanced_metrics['total_pnl']:.2f}")
    print(f"Sharpe Ratio: {enhanced_metrics['sharpe_ratio']:.4f}")
    print(f"Trades Blocked: Trend={enhanced_metrics['filter_blocks']['trend']}, "
          f"Vol={enhanced_metrics['filter_blocks']['volatility']}, "
          f"Session={enhanced_metrics['filter_blocks']['session']}")

    # Summary comparison
    print("\n" + "="*70)
    print("COMPARISON SUMMARY")
    print("="*70)

    results = {
        'Baseline (No Filters)': baseline_metrics,
        'Trend Filter Only': trend_metrics,
        'Volatility Filter Only': vol_metrics,
        'Session Filter Only': session_metrics,
        'All Filters Combined': enhanced_metrics
    }

    comparison_df = pd.DataFrame([
        {
            'Strategy': name,
            'Trades': m['total_trades'],
            'Win%': f"{m['win_rate']:.1%}",
            'Profit Factor': f"{m['profit_factor']:.3f}",
            'Total PnL': f"${m['total_pnl']:.0f}",
            'Sharpe': f"{m['sharpe_ratio']:.3f}",
            'Avg Win': f"${m['avg_win']:.0f}",
            'Avg Loss': f"${m['avg_loss']:.0f}"
        }
        for name, m in results.items()
    ])

    print(comparison_df.to_string(index=False))

    # Calculate improvements
    print("\n" + "="*70)
    print("IMPROVEMENT vs BASELINE")
    print("="*70)

    for name, metrics in results.items():
        if name == 'Baseline (No Filters)':
            continue

        win_rate_change = (metrics['win_rate'] - baseline_metrics['win_rate']) * 100
        pf_change = ((metrics['profit_factor'] - baseline_metrics['profit_factor']) /
                     baseline_metrics['profit_factor'] * 100) if baseline_metrics['profit_factor'] > 0 else 0
        pnl_change = metrics['total_pnl'] - baseline_metrics['total_pnl']

        print(f"\n{name}:")
        print(f"  Win Rate: {win_rate_change:+.1f} percentage points")
        print(f"  Profit Factor: {pf_change:+.1f}%")
        print(f"  Total PnL: ${pnl_change:+.0f}")

    # Save results
    os.makedirs(output_dir, exist_ok=True)
    comparison_df.to_csv(os.path.join(output_dir, 'filter_comparison.csv'), index=False)

    # Save detailed results
    with open(os.path.join(output_dir, 'detailed_results.txt'), 'w') as f:
        for name, metrics in results.items():
            f.write(f"\n{'='*70}\n")
            f.write(f"{name}\n")
            f.write(f"{'='*70}\n")
            for k, v in metrics.items():
                if k not in ['params', 'filter_blocks', 'filters_enabled']:
                    f.write(f"{k}: {v}\n")

    print(f"\n✓ Results saved to {output_dir}/")

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Enhanced backtesting with filters')
    parser.add_argument('--data', type=str, required=True, help='Historical data CSV')
    parser.add_argument('--output', type=str, default='./results_enhanced', help='Output directory')

    args = parser.parse_args()

    # Load data
    print(f"Loading data from {args.data}...")
    data = pd.read_csv(args.data)
    print(f"Loaded {len(data)} bars")

    # Run comparison
    results = run_comparison_test(data, args.output)

    print("\n" + "="*70)
    print("ENHANCED BACKTEST COMPLETE!")
    print("="*70)
    print(f"Results saved to: {args.output}/")
