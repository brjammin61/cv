"""
Module 8: Backtester

Validates Oracle strategies on historical data.
Calculates win rates, Sharpe ratios, drawdowns, and optimal parameters.
"""

import logging
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from modules import (
    BiasCorrector,
    FavoriteLongshotAdjuster,
    RiskFreeRateAdjuster,
    DutchBookDetector,
    SpatialArbitrageDetector
)

logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    """Container for backtest results."""
    strategy_name: str
    start_date: datetime
    end_date: datetime
    total_signals: int
    trades_taken: int
    wins: int
    losses: int
    win_rate: float
    total_return: float
    avg_return_per_trade: float
    sharpe_ratio: float
    max_drawdown: float
    avg_edge: float
    best_trade: float
    worst_trade: float
    equity_curve: List[float]


class Backtester:
    """
    Backtesting engine for Oracle strategies.

    Tests strategies on historical market data to validate performance
    before risking real capital.
    """

    def __init__(self, db_path: str = "data/oracle_data.db"):
        """
        Initialize backtester.

        Args:
            db_path (str): Path to database with historical data
        """
        self.db_path = db_path

        # Initialize analytical engines with default parameters
        self.engines = {
            'BiasCorrector': BiasCorrector(shy_voter_weight=0.75),
            'FLB': FavoriteLongshotAdjuster(),
            'RFR': RiskFreeRateAdjuster(risk_free_rate=0.05),
            'DutchBook': DutchBookDetector(),
            'SpatialArb': SpatialArbitrageDetector()
        }

        logger.info("Backtester initialized")

    def load_historical_data(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        market_id: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Load historical market data from database.

        Args:
            start_date: Start date for data
            end_date: End date for data
            market_id: Specific market ID to load

        Returns:
            DataFrame with historical snapshots
        """
        conn = sqlite3.connect(self.db_path)

        query = "SELECT * FROM market_snapshots WHERE 1=1"
        params = []

        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)

        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)

        if market_id:
            query += " AND market_id = ?"
            params.append(market_id)

        query += " ORDER BY timestamp"

        df = pd.read_sql_query(query, conn, params=params if params else None)
        conn.close()

        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        logger.info(f"Loaded {len(df)} historical snapshots")

        return df

    def backtest_spatial_arbitrage(
        self,
        data: pd.DataFrame,
        min_edge: float = 1.0,
        holding_period_hours: int = 24
    ) -> BacktestResult:
        """
        Backtest spatial arbitrage strategy.

        Args:
            data: Historical market data
            min_edge: Minimum edge to take trade (cents)
            holding_period_hours: How long to hold position

        Returns:
            BacktestResult
        """
        logger.info("Backtesting Spatial Arbitrage strategy...")

        # Find markets that exist on both exchanges
        markets_on_both = data.groupby('market_name')['exchange'].nunique()
        markets_on_both = markets_on_both[markets_on_both >= 2].index.tolist()

        logger.info(f"Found {len(markets_on_both)} markets on both exchanges")

        trades = []

        for market in markets_on_both:
            market_data = data[data['market_name'] == market].copy()

            # Pivot to have kalshi and polymarket side by side
            kalshi_data = market_data[market_data['exchange'] == 'kalshi'][
                ['timestamp', 'best_bid', 'best_ask', 'mid_price']
            ].rename(columns={'best_bid': 'k_bid', 'best_ask': 'k_ask', 'mid_price': 'k_mid'})

            poly_data = market_data[market_data['exchange'] == 'polymarket'][
                ['timestamp', 'best_bid', 'best_ask', 'mid_price']
            ].rename(columns={'best_bid': 'p_bid', 'best_ask': 'p_ask', 'mid_price': 'p_mid'})

            # Merge on timestamp (fuzzy matching within 5 minutes)
            combined = pd.merge_asof(
                kalshi_data.sort_values('timestamp'),
                poly_data.sort_values('timestamp'),
                on='timestamp',
                direction='nearest',
                tolerance=pd.Timedelta('5min')
            )

            # Drop rows with NaN
            combined = combined.dropna()

            # Check for arbitrage opportunities
            for idx, row in combined.iterrows():
                signal, rationale = self.engines['SpatialArb'].find_arbitrage(
                    row['k_bid'], row['k_ask'],
                    row['p_bid'], row['p_ask']
                )

                if signal != 'HOLD':
                    # Calculate edge
                    if signal == 'BUY_KALSHI_SELL_POLY':
                        edge = (row['p_bid'] - row['k_ask']) * 100
                        entry_price = row['k_ask']
                        venue = 'kalshi'
                    else:  # BUY_POLY_SELL_KALSHI
                        edge = (row['k_bid'] - row['p_ask']) * 100
                        entry_price = row['p_ask']
                        venue = 'polymarket'

                    if edge >= min_edge:
                        # Find exit price (after holding period)
                        exit_time = row['timestamp'] + timedelta(hours=holding_period_hours)
                        exit_data = combined[combined['timestamp'] >= exit_time].head(1)

                        if not exit_data.empty:
                            if venue == 'kalshi':
                                exit_price = exit_data.iloc[0]['k_mid']
                            else:
                                exit_price = exit_data.iloc[0]['p_mid']

                            # Calculate P&L
                            pnl = (exit_price - entry_price) * 100  # cents

                            trades.append({
                                'timestamp': row['timestamp'],
                                'market': market,
                                'signal': signal,
                                'edge': edge,
                                'entry_price': entry_price,
                                'exit_price': exit_price,
                                'pnl': pnl,
                                'holding_period_hours': holding_period_hours
                            })

        # Calculate results
        if not trades:
            logger.warning("No trades found in backtest period")
            return self._empty_result("SpatialArbitrage")

        trades_df = pd.DataFrame(trades)

        return self._calculate_results("SpatialArbitrage", trades_df, data['timestamp'].min(), data['timestamp'].max())

    def backtest_bias_correction(
        self,
        data: pd.DataFrame,
        polling_data: Optional[pd.DataFrame] = None,
        min_conviction: str = "MEDIUM"
    ) -> BacktestResult:
        """
        Backtest bias correction strategy.

        Note: Requires historical polling data (self vs neighbor).
        If not available, this will return limited results.

        Args:
            data: Historical market data
            polling_data: Historical polling data with 'self_pref' and 'neighbor_pref'
            min_conviction: Minimum conviction to take trade

        Returns:
            BacktestResult
        """
        logger.info("Backtesting Bias Correction strategy...")

        if polling_data is None or polling_data.empty:
            logger.warning("No polling data available for bias correction backtest")
            return self._empty_result("BiasCorrector")

        # This is a simplified version - in production, you'd match polling data
        # to market data by date and market
        logger.warning("Bias correction backtesting requires manual polling data integration")

        return self._empty_result("BiasCorrector")

    def backtest_all_strategies(
        self,
        days: int = 30,
        min_edge: float = 1.0
    ) -> Dict[str, BacktestResult]:
        """
        Run backtests for all strategies.

        Args:
            days: Number of days to backtest
            min_edge: Minimum edge to take trades

        Returns:
            Dict mapping strategy name to BacktestResult
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        logger.info(f"Running backtests from {start_date} to {end_date}")

        # Load historical data
        data = self.load_historical_data(start_date=start_date, end_date=end_date)

        if data.empty:
            logger.error("No historical data available for backtesting")
            return {}

        results = {}

        # Spatial Arbitrage
        try:
            results['SpatialArbitrage'] = self.backtest_spatial_arbitrage(
                data, min_edge=min_edge
            )
        except Exception as e:
            logger.error(f"Spatial Arbitrage backtest failed: {e}")

        # Add other strategies as they become implementable

        return results

    def _calculate_results(
        self,
        strategy_name: str,
        trades_df: pd.DataFrame,
        start_date: datetime,
        end_date: datetime
    ) -> BacktestResult:
        """Calculate backtest metrics from trades DataFrame."""

        total_signals = len(trades_df)
        trades_taken = total_signals  # In backtest, we take all signals

        # Win/Loss
        wins = (trades_df['pnl'] > 0).sum()
        losses = (trades_df['pnl'] < 0).sum()
        win_rate = (wins / trades_taken * 100) if trades_taken > 0 else 0

        # Returns
        total_return = trades_df['pnl'].sum()
        avg_return = trades_df['pnl'].mean()

        # Sharpe Ratio (simplified - assumes daily returns)
        returns = trades_df['pnl']
        sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0

        # Max Drawdown
        cumulative = returns.cumsum()
        running_max = cumulative.expanding().max()
        drawdown = cumulative - running_max
        max_drawdown = drawdown.min()

        # Edge
        avg_edge = trades_df['edge'].mean()

        # Best/Worst
        best_trade = trades_df['pnl'].max()
        worst_trade = trades_df['pnl'].min()

        # Equity curve
        equity_curve = cumulative.tolist()

        return BacktestResult(
            strategy_name=strategy_name,
            start_date=start_date,
            end_date=end_date,
            total_signals=total_signals,
            trades_taken=trades_taken,
            wins=wins,
            losses=losses,
            win_rate=win_rate,
            total_return=total_return,
            avg_return_per_trade=avg_return,
            sharpe_ratio=sharpe,
            max_drawdown=max_drawdown,
            avg_edge=avg_edge,
            best_trade=best_trade,
            worst_trade=worst_trade,
            equity_curve=equity_curve
        )

    def _empty_result(self, strategy_name: str) -> BacktestResult:
        """Return empty result when no data available."""
        return BacktestResult(
            strategy_name=strategy_name,
            start_date=datetime.now(),
            end_date=datetime.now(),
            total_signals=0,
            trades_taken=0,
            wins=0,
            losses=0,
            win_rate=0,
            total_return=0,
            avg_return_per_trade=0,
            sharpe_ratio=0,
            max_drawdown=0,
            avg_edge=0,
            best_trade=0,
            worst_trade=0,
            equity_curve=[]
        )

    def print_backtest_report(self, results: Dict[str, BacktestResult]):
        """Print formatted backtest report."""
        print("\n" + "=" * 80)
        print("BACKTEST RESULTS")
        print("=" * 80)

        for strategy, result in results.items():
            print(f"\n📊 {result.strategy_name}")
            print("-" * 80)
            print(f"Period: {result.start_date.date()} to {result.end_date.date()}")
            print(f"Total Signals: {result.total_signals}")
            print(f"Trades Taken: {result.trades_taken}")

            print(f"\n🎯 Performance:")
            print(f"  Win Rate: {result.win_rate:.1f}% ({result.wins}W / {result.losses}L)")
            print(f"  Total Return: {result.total_return:+.2f}¢")
            print(f"  Avg Return/Trade: {result.avg_return_per_trade:+.2f}¢")

            print(f"\n📈 Risk Metrics:")
            print(f"  Sharpe Ratio: {result.sharpe_ratio:.2f}")
            print(f"  Max Drawdown: {result.max_drawdown:.2f}¢")

            print(f"\n💰 Edge:")
            print(f"  Average Edge: {result.avg_edge:.2f}¢")
            print(f"  Best Trade: {result.best_trade:+.2f}¢")
            print(f"  Worst Trade: {result.worst_trade:+.2f}¢")

        print("\n" + "=" * 80)


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 80)
    print("BACKTESTER - Module 8")
    print("=" * 80)

    backtester = Backtester()

    print("\n[1] Loading historical data...")
    data = backtester.load_historical_data(
        start_date=datetime.now() - timedelta(days=7)
    )

    print(f"✅ Loaded {len(data)} snapshots")

    if not data.empty:
        print("\n[2] Running backtests...")
        results = backtester.backtest_all_strategies(days=7, min_edge=1.0)

        print("\n[3] Results:")
        backtester.print_backtest_report(results)
    else:
        print("\n⚠️  No historical data yet. Run data collector first!")
        print("   python -c 'from modules.mod_06_data_collector import DataCollector; DataCollector().run_collection_cycle()'")
