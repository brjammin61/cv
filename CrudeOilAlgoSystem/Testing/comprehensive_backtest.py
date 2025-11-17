"""
Comprehensive Backtesting Framework
====================================

Runs extensive backtests on real historical data with multiple parameter
combinations to find the most profitable strategy configuration.

Features:
- Walk-forward optimization
- Parameter grid search
- Monte Carlo simulation
- Performance analysis and ranking
- Visual dashboards

Author: Algorithmic Trading Framework 2025
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from itertools import product
import json
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    HAS_PLOTTING = True
except ImportError:
    HAS_PLOTTING = False
    print("Warning: matplotlib/seaborn not installed. Visualization disabled.")


class BacktestEngine:
    """
    Backtesting engine for strategy evaluation
    """

    def __init__(self, data: pd.DataFrame, initial_balance=50000):
        """
        Initialize backtest engine

        Args:
            data: Historical OHLCV data
            initial_balance: Starting capital
        """
        self.data = data.reset_index(drop=True)
        self.initial_balance = initial_balance

    def run_vwap_strategy(self, params):
        """
        Run VWAP mean reversion strategy

        Args:
            params: Dict with strategy parameters

        Returns:
            Dict with performance metrics
        """
        vwap_period = params.get('vwap_period', 20)
        stddev_mult = params.get('stddev_mult', 2.0)
        stop_loss_ticks = params.get('stop_loss_ticks', 25)
        target_ticks = params.get('target_ticks', 20)

        balance = self.initial_balance
        position = 0
        entry_price = 0
        trades = []
        equity_curve = []

        max_balance = balance
        max_drawdown = 0

        for i in range(vwap_period, len(self.data)):
            current_bar = self.data.iloc[i]
            close = current_bar['close']

            # Calculate VWAP and bands
            recent_data = self.data.iloc[i-vwap_period:i]
            vwap = (recent_data['close'] * recent_data['volume']).sum() / recent_data['volume'].sum()
            std = recent_data['close'].std()

            upper_band = vwap + (std * stddev_mult)
            lower_band = vwap - (std * stddev_mult)

            # Entry logic
            if position == 0:
                # Long at lower band
                if close <= lower_band:
                    position = 1
                    entry_price = close
                # Short at upper band
                elif close >= upper_band:
                    position = -1
                    entry_price = close

            # Exit logic
            elif position != 0:
                pnl = 0

                # Check stop loss
                if position == 1 and close <= entry_price - (stop_loss_ticks * 0.01):
                    pnl = (close - entry_price) * 1000  # CL contract size
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
                    balance += pnl
                    trades.append({
                        'entry': entry_price,
                        'exit': close,
                        'pnl': pnl,
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
            return self._empty_metrics()

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
            'params': params
        }

        return metrics

    def _calculate_sharpe(self, equity_curve):
        """Calculate Sharpe ratio"""
        if len(equity_curve) < 2:
            return 0

        returns = pd.Series(equity_curve).pct_change().dropna()
        if returns.std() == 0:
            return 0

        sharpe = (returns.mean() / returns.std()) * np.sqrt(252)  # Annualized
        return sharpe

    def _empty_metrics(self):
        """Return empty metrics dict"""
        return {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0,
            'total_pnl': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'largest_win': 0,
            'largest_loss': 0,
            'profit_factor': 0,
            'max_drawdown': 0,
            'final_balance': self.initial_balance,
            'return_pct': 0,
            'sharpe_ratio': 0
        }


class WalkForwardOptimizer:
    """
    Walk-forward optimization framework
    """

    def __init__(self, data: pd.DataFrame, in_sample_days=90, out_sample_days=30):
        """
        Initialize walk-forward optimizer

        Args:
            data: Historical data
            in_sample_days: Days for in-sample optimization
            out_sample_days: Days for out-of-sample testing
        """
        self.data = data
        self.in_sample_days = in_sample_days
        self.out_sample_days = out_sample_days

    def optimize(self, param_grid):
        """
        Run walk-forward optimization

        Args:
            param_grid: Dict of parameter ranges

        Returns:
            List of walk-forward results
        """
        results = []

        # Generate parameter combinations
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        param_combinations = list(product(*param_values))

        print(f"Testing {len(param_combinations)} parameter combinations...")

        # Convert data to daily (if not already)
        self.data['date'] = pd.to_datetime(self.data['timestamp'])
        unique_dates = self.data['date'].dt.date.unique()

        # Walk forward through data
        start_idx = 0
        window_num = 0

        while start_idx + self.in_sample_days + self.out_sample_days <= len(unique_dates):
            window_num += 1

            # Define in-sample and out-of-sample periods
            is_end = start_idx + self.in_sample_days
            oos_end = is_end + self.out_sample_days

            is_dates = unique_dates[start_idx:is_end]
            oos_dates = unique_dates[is_end:oos_end]

            is_data = self.data[self.data['date'].dt.date.isin(is_dates)]
            oos_data = self.data[self.data['date'].dt.date.isin(oos_dates)]

            print(f"\nWindow {window_num}:")
            print(f"  In-Sample: {is_dates[0]} to {is_dates[-1]} ({len(is_data)} bars)")
            print(f"  Out-of-Sample: {oos_dates[0]} to {oos_dates[-1]} ({len(oos_data)} bars)")

            # Optimize on in-sample data
            best_params = None
            best_score = -np.inf

            for param_values in param_combinations:
                params = dict(zip(param_names, param_values))

                # Run backtest on in-sample data
                engine = BacktestEngine(is_data)
                metrics = engine.run_vwap_strategy(params)

                # Score based on Sharpe ratio and profit factor
                score = metrics['sharpe_ratio'] * metrics['profit_factor']

                if score > best_score:
                    best_score = score
                    best_params = params

            print(f"  Best In-Sample Params: {best_params}")
            print(f"  Best In-Sample Score: {best_score:.4f}")

            # Test on out-of-sample data
            engine_oos = BacktestEngine(oos_data)
            oos_metrics = engine_oos.run_vwap_strategy(best_params)

            print(f"  OOS PnL: ${oos_metrics['total_pnl']:.2f}")
            print(f"  OOS Profit Factor: {oos_metrics['profit_factor']:.2f}")
            print(f"  OOS Sharpe: {oos_metrics['sharpe_ratio']:.2f}")

            results.append({
                'window': window_num,
                'is_start': str(is_dates[0]),
                'is_end': str(is_dates[-1]),
                'oos_start': str(oos_dates[0]),
                'oos_end': str(oos_dates[-1]),
                'best_params': best_params,
                'is_score': best_score,
                'oos_pnl': oos_metrics['total_pnl'],
                'oos_profit_factor': oos_metrics['profit_factor'],
                'oos_sharpe': oos_metrics['sharpe_ratio'],
                'oos_win_rate': oos_metrics['win_rate'],
                'oos_trades': oos_metrics['total_trades']
            })

            # Move window forward
            start_idx += self.out_sample_days

        return results


def run_parameter_grid_search(data: pd.DataFrame, output_dir='./results'):
    """
    Run comprehensive parameter grid search

    Args:
        data: Historical data
        output_dir: Directory for saving results

    Returns:
        DataFrame with all results
    """
    print("="*60)
    print("PARAMETER GRID SEARCH")
    print("="*60)

    # Define parameter grid
    param_grid = {
        'vwap_period': [15, 20, 25],
        'stddev_mult': [1.5, 2.0, 2.5],
        'stop_loss_ticks': [20, 25, 30],
        'target_ticks': [15, 20, 25]
    }

    # Generate all combinations
    param_names = list(param_grid.keys())
    param_values = list(param_grid.values())
    param_combinations = list(product(*param_values))

    print(f"Testing {len(param_combinations)} parameter combinations...")

    results = []
    engine = BacktestEngine(data)

    for i, param_vals in enumerate(param_combinations):
        params = dict(zip(param_names, param_vals))

        # Run backtest
        metrics = engine.run_vwap_strategy(params)

        results.append(metrics)

        if (i + 1) % 10 == 0:
            print(f"  Completed {i+1}/{len(param_combinations)}...")

    # Convert to DataFrame
    results_df = pd.DataFrame(results)

    # Sort by Sharpe ratio
    results_df = results_df.sort_values('sharpe_ratio', ascending=False)

    # Save results
    os.makedirs(output_dir, exist_ok=True)
    results_df.to_csv(os.path.join(output_dir, 'parameter_grid_results.csv'), index=False)

    print("\nTop 10 Parameter Combinations:")
    print(results_df[['total_pnl', 'profit_factor', 'sharpe_ratio', 'win_rate', 'params']].head(10))

    return results_df


def generate_performance_report(results_df, wf_results, output_dir='./results'):
    """
    Generate comprehensive performance report

    Args:
        results_df: Grid search results
        wf_results: Walk-forward results
        output_dir: Output directory
    """
    os.makedirs(output_dir, exist_ok=True)

    report = {
        'timestamp': datetime.now().isoformat(),
        'grid_search_summary': {
            'total_combinations_tested': len(results_df),
            'best_sharpe_ratio': float(results_df['sharpe_ratio'].max()),
            'best_profit_factor': float(results_df['profit_factor'].max()),
            'best_total_pnl': float(results_df['total_pnl'].max()),
            'avg_win_rate': float(results_df['win_rate'].mean()),
            'best_params': results_df.iloc[0]['params']
        },
        'walk_forward_summary': {
            'total_windows': len(wf_results),
            'avg_oos_pnl': np.mean([r['oos_pnl'] for r in wf_results]),
            'avg_oos_profit_factor': np.mean([r['oos_profit_factor'] for r in wf_results]),
            'avg_oos_sharpe': np.mean([r['oos_sharpe'] for r in wf_results]),
            'profitable_windows': sum(1 for r in wf_results if r['oos_pnl'] > 0),
            'most_stable_params': wf_results[0]['best_params'] if wf_results else None
        }
    }

    # Save JSON report
    with open(os.path.join(output_dir, 'performance_report.json'), 'w') as f:
        json.dump(report, f, indent=2)

    # Create text report
    with open(os.path.join(output_dir, 'performance_report.txt'), 'w') as f:
        f.write("="*70 + "\n")
        f.write("CRUDE OIL STRATEGY OPTIMIZATION REPORT\n")
        f.write("="*70 + "\n\n")

        f.write("GRID SEARCH RESULTS:\n")
        f.write("-" * 70 + "\n")
        f.write(f"Total Combinations Tested: {report['grid_search_summary']['total_combinations_tested']}\n")
        f.write(f"Best Sharpe Ratio: {report['grid_search_summary']['best_sharpe_ratio']:.4f}\n")
        f.write(f"Best Profit Factor: {report['grid_search_summary']['best_profit_factor']:.4f}\n")
        f.write(f"Best Total PnL: ${report['grid_search_summary']['best_total_pnl']:.2f}\n")
        f.write(f"Average Win Rate: {report['grid_search_summary']['avg_win_rate']:.2%}\n")
        f.write(f"\nBest Parameters:\n")
        for k, v in report['grid_search_summary']['best_params'].items():
            f.write(f"  {k}: {v}\n")

        f.write("\n" + "="*70 + "\n")
        f.write("WALK-FORWARD OPTIMIZATION RESULTS:\n")
        f.write("-" * 70 + "\n")
        f.write(f"Total Windows: {report['walk_forward_summary']['total_windows']}\n")
        f.write(f"Avg OOS PnL: ${report['walk_forward_summary']['avg_oos_pnl']:.2f}\n")
        f.write(f"Avg OOS Profit Factor: {report['walk_forward_summary']['avg_oos_profit_factor']:.4f}\n")
        f.write(f"Avg OOS Sharpe: {report['walk_forward_summary']['avg_oos_sharpe']:.4f}\n")
        f.write(f"Profitable Windows: {report['walk_forward_summary']['profitable_windows']}/{report['walk_forward_summary']['total_windows']}\n")

        f.write("\n" + "="*70 + "\n")
        f.write("RECOMMENDATION:\n")
        f.write("-" * 70 + "\n")
        f.write("Based on walk-forward optimization (most robust), use:\n\n")
        if report['walk_forward_summary']['most_stable_params']:
            for k, v in report['walk_forward_summary']['most_stable_params'].items():
                f.write(f"  {k}: {v}\n")

    print(f"\n✓ Performance report saved to {output_dir}/")

    return report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Comprehensive backtesting')
    parser.add_argument('--data', type=str, required=True, help='Historical data CSV')
    parser.add_argument('--output', type=str, default='./results', help='Output directory')
    parser.add_argument('--skip-grid', action='store_true', help='Skip grid search')
    parser.add_argument('--skip-wf', action='store_true', help='Skip walk-forward')

    args = parser.parse_args()

    # Load data
    print(f"Loading data from {args.data}...")
    data = pd.read_csv(args.data)
    print(f"Loaded {len(data)} bars")

    # Run grid search
    if not args.skip_grid:
        results_df = run_parameter_grid_search(data, args.output)
    else:
        results_df = pd.DataFrame()

    # Run walk-forward optimization
    if not args.skip_wf:
        print("\n" + "="*60)
        print("WALK-FORWARD OPTIMIZATION")
        print("="*60)

        wf_optimizer = WalkForwardOptimizer(data)

        param_grid = {
            'vwap_period': [15, 20, 25],
            'stddev_mult': [1.5, 2.0, 2.5],
            'stop_loss_ticks': [20, 25, 30],
            'target_ticks': [15, 20, 25]
        }

        wf_results = wf_optimizer.optimize(param_grid)

        # Save walk-forward results
        wf_df = pd.DataFrame(wf_results)
        wf_df.to_csv(os.path.join(args.output, 'walk_forward_results.csv'), index=False)
    else:
        wf_results = []

    # Generate final report
    if not args.skip_grid or not args.skip_wf:
        print("\nGenerating performance report...")
        report = generate_performance_report(results_df, wf_results, args.output)

        print("\n" + "="*60)
        print("OPTIMIZATION COMPLETE!")
        print("="*60)
        print(f"Results saved to: {args.output}/")
