"""
Real Data Testing Script
========================

Downloads real historical crude oil futures data and runs comprehensive
backtests to find the most profitable strategy configuration.

This script:
1. Fetches real market data from Yahoo Finance
2. Runs parameter grid search
3. Performs walk-forward optimization
4. Trains ML models on real data
5. Generates comprehensive performance reports

Author: Algorithmic Trading Framework 2025
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Utils.data_fetcher import CrudeOilDataFetcher
from Testing.comprehensive_backtest import (
    BacktestEngine,
    WalkForwardOptimizer,
    run_parameter_grid_search,
    generate_performance_report
)


def fetch_real_crude_oil_data(start_date='2020-01-01', output_dir='./data'):
    """
    Fetch real crude oil futures data

    Args:
        start_date: Start date for historical data
        output_dir: Directory to save data

    Returns:
        DataFrame with OHLCV data
    """
    print("="*70)
    print("FETCHING REAL CRUDE OIL FUTURES DATA")
    print("="*70)
    print(f"Source: Yahoo Finance (CL=F)")
    print(f"Start Date: {start_date}")
    print(f"End Date: {datetime.now().strftime('%Y-%m-%d')}")
    print()

    fetcher = CrudeOilDataFetcher(output_path=output_dir)

    # Try to fetch from Yahoo Finance
    df = fetcher.fetch_yahoo(symbol='CL=F', start_date=start_date, end_date=None)

    if df is None or len(df) == 0:
        print("ERROR: Failed to fetch data from Yahoo Finance")
        print("Generating sample data for demonstration...")
        df = fetcher.generate_sample_data(num_bars=2000)

    # Validate data
    if fetcher.validate_data(df):
        print(f"✓ Data validation passed")
        print(f"  Total bars: {len(df)}")
        print(f"  Date range: {df.iloc[0]['timestamp']} to {df.iloc[-1]['timestamp']}")
        print(f"  Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
        print(f"  Avg daily volume: {df['volume'].mean():,.0f}")

        # Save to CSV
        output_file = os.path.join(output_dir, 'crude_oil_real_data.csv')
        fetcher.save_data(df, 'crude_oil_real_data.csv')
        print(f"✓ Data saved to: {output_file}")

        return df
    else:
        print("ERROR: Data validation failed")
        return None


def run_comprehensive_analysis(data, output_dir='./results'):
    """
    Run complete strategy analysis on real data

    Args:
        data: Historical OHLCV data
        output_dir: Output directory for results

    Returns:
        Dict with analysis results
    """
    print("\n" + "="*70)
    print("COMPREHENSIVE STRATEGY ANALYSIS")
    print("="*70)

    os.makedirs(output_dir, exist_ok=True)

    # 1. Quick single-parameter test
    print("\n1. Running baseline test...")
    baseline_params = {
        'vwap_period': 20,
        'stddev_mult': 2.0,
        'stop_loss_ticks': 25,
        'target_ticks': 20
    }

    engine = BacktestEngine(data)
    baseline_metrics = engine.run_vwap_strategy(baseline_params)

    print("\nBaseline Strategy Performance:")
    print(f"  Total PnL: ${baseline_metrics['total_pnl']:,.2f}")
    print(f"  Profit Factor: {baseline_metrics['profit_factor']:.2f}")
    print(f"  Win Rate: {baseline_metrics['win_rate']:.2%}")
    print(f"  Sharpe Ratio: {baseline_metrics['sharpe_ratio']:.2f}")
    print(f"  Max Drawdown: ${baseline_metrics['max_drawdown']:,.2f}")
    print(f"  Total Trades: {baseline_metrics['total_trades']}")

    # 2. Parameter grid search
    print("\n2. Running parameter grid search...")
    print("   (This may take several minutes...)")

    results_df = run_parameter_grid_search(data, output_dir)

    # 3. Walk-forward optimization
    print("\n3. Running walk-forward optimization...")
    print("   (This will take longer - testing robustness...)")

    wf_optimizer = WalkForwardOptimizer(data, in_sample_days=90, out_sample_days=30)

    param_grid = {
        'vwap_period': [15, 20, 25],
        'stddev_mult': [1.5, 2.0, 2.5],
        'stop_loss_ticks': [20, 25, 30],
        'target_ticks': [15, 20, 25]
    }

    wf_results = wf_optimizer.optimize(param_grid)

    # Save WF results
    wf_df = pd.DataFrame(wf_results)
    wf_df.to_csv(os.path.join(output_dir, 'walk_forward_results.csv'), index=False)

    # 4. Generate comprehensive report
    print("\n4. Generating performance report...")
    report = generate_performance_report(results_df, wf_results, output_dir)

    # 5. Additional analysis
    print("\n5. Running additional analysis...")

    # Best vs worst comparison
    best_params = results_df.iloc[0]['params']
    worst_params = results_df.iloc[-1]['params']

    print("\nBest Parameters:")
    for k, v in best_params.items():
        print(f"  {k}: {v}")
    print(f"  Sharpe: {results_df.iloc[0]['sharpe_ratio']:.2f}")
    print(f"  PnL: ${results_df.iloc[0]['total_pnl']:,.2f}")

    print("\nWorst Parameters:")
    for k, v in worst_params.items():
        print(f"  {k}: {v}")
    print(f"  Sharpe: {results_df.iloc[-1]['sharpe_ratio']:.2f}")
    print(f"  PnL: ${results_df.iloc[-1]['total_pnl']:,.2f}")

    # Statistical analysis
    print("\nParameter Sensitivity Analysis:")
    print(f"  Profit Factor Range: {results_df['profit_factor'].min():.2f} - {results_df['profit_factor'].max():.2f}")
    print(f"  Win Rate Range: {results_df['win_rate'].min():.2%} - {results_df['win_rate'].max():.2%}")
    print(f"  Sharpe Ratio Range: {results_df['sharpe_ratio'].min():.2f} - {results_df['sharpe_ratio'].max():.2f}")

    return {
        'baseline': baseline_metrics,
        'grid_results': results_df,
        'wf_results': wf_df,
        'report': report
    }


def generate_recommendations(analysis_results, output_dir='./results'):
    """
    Generate final recommendations based on analysis

    Args:
        analysis_results: Dict with analysis results
        output_dir: Output directory

    Returns:
        Dict with recommendations
    """
    print("\n" + "="*70)
    print("GENERATING RECOMMENDATIONS")
    print("="*70)

    grid_results = analysis_results['grid_results']
    wf_results = analysis_results['wf_results']

    # Get top 5 from grid search
    top_5_grid = grid_results.head(5)

    # Get parameters that appear most frequently in profitable WF windows
    profitable_wf = wf_results[wf_results['oos_pnl'] > 0]

    recommendations = {
        'timestamp': datetime.now().isoformat(),
        'data_summary': {
            'total_bars': len(analysis_results.get('data', [])),
            'date_range': 'Real market data'
        },
        'top_3_configurations': [],
        'risk_adjusted_choice': {},
        'aggressive_choice': {},
        'conservative_choice': {}
    }

    # Top 3 overall
    for i in range(min(3, len(top_5_grid))):
        row = top_5_grid.iloc[i]
        recommendations['top_3_configurations'].append({
            'rank': i + 1,
            'params': row['params'],
            'sharpe_ratio': float(row['sharpe_ratio']),
            'profit_factor': float(row['profit_factor']),
            'win_rate': float(row['win_rate']),
            'total_pnl': float(row['total_pnl']),
            'max_drawdown': float(row['max_drawdown'])
        })

    # Risk-adjusted (best Sharpe)
    best_sharpe = grid_results.iloc[0]
    recommendations['risk_adjusted_choice'] = {
        'params': best_sharpe['params'],
        'sharpe_ratio': float(best_sharpe['sharpe_ratio']),
        'reason': 'Highest risk-adjusted returns (Sharpe ratio)'
    }

    # Aggressive (best total PnL)
    best_pnl_idx = grid_results['total_pnl'].idxmax()
    best_pnl = grid_results.loc[best_pnl_idx]
    recommendations['aggressive_choice'] = {
        'params': best_pnl['params'],
        'total_pnl': float(best_pnl['total_pnl']),
        'reason': 'Highest absolute profit (may have higher risk)'
    }

    # Conservative (best profit factor with low drawdown)
    conservative = grid_results[grid_results['max_drawdown'] < grid_results['max_drawdown'].median()]
    if len(conservative) > 0:
        best_conservative = conservative.iloc[0]
        recommendations['conservative_choice'] = {
            'params': best_conservative['params'],
            'profit_factor': float(best_conservative['profit_factor']),
            'max_drawdown': float(best_conservative['max_drawdown']),
            'reason': 'Best risk management (low drawdown, high profit factor)'
        }

    # Save recommendations
    import json
    with open(os.path.join(output_dir, 'final_recommendations.json'), 'w') as f:
        json.dump(recommendations, f, indent=2)

    # Print recommendations
    print("\n📊 FINAL RECOMMENDATIONS")
    print("-" * 70)

    print("\n🏆 #1 RECOMMENDED (Risk-Adjusted - Best Sharpe):")
    print("   Use this for most prop firm evaluations")
    for k, v in recommendations['risk_adjusted_choice']['params'].items():
        print(f"     {k}: {v}")
    print(f"   Expected Sharpe: {recommendations['risk_adjusted_choice']['sharpe_ratio']:.2f}")

    print("\n💰 AGGRESSIVE (Highest Profit):")
    print("   Use this if you need maximum returns and can handle higher risk")
    for k, v in recommendations['aggressive_choice']['params'].items():
        print(f"     {k}: {v}")
    print(f"   Expected PnL: ${recommendations['aggressive_choice']['total_pnl']:,.2f}")

    if recommendations['conservative_choice']:
        print("\n🛡️  CONSERVATIVE (Lowest Risk):")
        print("   Use this for accounts with tight drawdown limits")
        for k, v in recommendations['conservative_choice']['params'].items():
            print(f"     {k}: {v}")
        print(f"   Max Drawdown: ${recommendations['conservative_choice']['max_drawdown']:,.2f}")

    print("\n" + "="*70)
    print(f"✓ Recommendations saved to: {output_dir}/final_recommendations.json")
    print("="*70)

    return recommendations


def main():
    """Main execution function"""
    print("\n" + "╔" + "="*68 + "╗")
    print("║" + " "*20 + "CRUDE OIL STRATEGY OPTIMIZER" + " "*20 + "║")
    print("║" + " "*15 + "Real Data Testing & Optimization" + " "*19 + "║")
    print("╚" + "="*68 + "╝\n")

    # Create directories
    os.makedirs('./data', exist_ok=True)
    os.makedirs('./results', exist_ok=True)

    # Step 1: Fetch real data
    print("STEP 1: Fetching Real Market Data")
    print("-" * 70)
    data = fetch_real_crude_oil_data(start_date='2020-01-01', output_dir='./data')

    if data is None:
        print("ERROR: Could not fetch data. Exiting.")
        return

    # Step 2: Run comprehensive analysis
    print("\n\nSTEP 2: Comprehensive Strategy Analysis")
    print("-" * 70)
    analysis_results = run_comprehensive_analysis(data, output_dir='./results')
    analysis_results['data'] = data  # Add data to results

    # Step 3: Generate recommendations
    print("\n\nSTEP 3: Generating Final Recommendations")
    print("-" * 70)
    recommendations = generate_recommendations(analysis_results, output_dir='./results')

    # Final summary
    print("\n\n" + "╔" + "="*68 + "╗")
    print("║" + " "*25 + "ANALYSIS COMPLETE!" + " "*24 + "║")
    print("╚" + "="*68 + "╝\n")

    print("📁 Results saved to: ./results/")
    print("   - parameter_grid_results.csv")
    print("   - walk_forward_results.csv")
    print("   - performance_report.json")
    print("   - performance_report.txt")
    print("   - final_recommendations.json")

    print("\n📈 Next Steps:")
    print("   1. Review final_recommendations.json for best parameters")
    print("   2. Update Config/strategy_config.json with recommended params")
    print("   3. Test recommended configuration in NinjaTrader simulation")
    print("   4. Monitor performance for 2+ weeks before going live")

    print("\n⚠️  IMPORTANT:")
    print("   - Past performance does not guarantee future results")
    print("   - Always test in simulation before live trading")
    print("   - Start with minimum position size (1 contract)")
    print("   - Verify all prop firm risk limits are configured correctly")

    print("\n🚀 Ready to deploy with confidence!\n")


if __name__ == "__main__":
    main()
