"""
Historical Data Fetcher for Crude Oil Futures
==============================================

Fetches and prepares historical crude oil futures data for backtesting and model training.

Supports multiple data sources:
- Yahoo Finance (free, limited)
- Quandl (API key required)
- Direct CSV import

Author: Algorithmic Trading Framework 2025
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import argparse
import os


class CrudeOilDataFetcher:
    """
    Fetches historical crude oil futures data
    """

    def __init__(self, output_path: str = "./data"):
        """
        Initialize data fetcher

        Args:
            output_path: Directory to save fetched data
        """
        self.output_path = output_path
        os.makedirs(output_path, exist_ok=True)

    def fetch_yahoo(self, symbol: str = "CL=F", start_date: str = "2020-01-01", end_date: str = None):
        """
        Fetch data from Yahoo Finance

        Args:
            symbol: Ticker symbol (CL=F for Crude Oil Futures)
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (default: today)

        Returns:
            DataFrame with OHLCV data
        """
        try:
            import yfinance as yf

            if end_date is None:
                end_date = datetime.now().strftime("%Y-%m-%d")

            print(f"Fetching {symbol} data from Yahoo Finance...")
            print(f"Date range: {start_date} to {end_date}")

            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date, interval="1d")

            if df.empty:
                raise ValueError("No data retrieved from Yahoo Finance")

            # Standardize column names
            df.columns = [col.lower() for col in df.columns]
            df = df.reset_index()
            df['timestamp'] = df['date'].dt.strftime("%Y-%m-%d %H:%M:%S")

            # Select required columns
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

            print(f"Retrieved {len(df)} bars")

            return df

        except ImportError:
            print("Error: yfinance not installed. Install with: pip install yfinance")
            return None
        except Exception as e:
            print(f"Error fetching Yahoo Finance data: {e}")
            return None

    def fetch_quandl(self, api_key: str, dataset: str = "CHRIS/CME_CL1", start_date: str = "2020-01-01"):
        """
        Fetch data from Quandl (requires API key)

        Args:
            api_key: Quandl API key
            dataset: Quandl dataset code
            start_date: Start date in YYYY-MM-DD format

        Returns:
            DataFrame with OHLCV data
        """
        try:
            import quandl

            quandl.ApiConfig.api_key = api_key

            print(f"Fetching {dataset} from Quandl...")

            df = quandl.get(dataset, start_date=start_date)

            # Standardize column names
            df = df.reset_index()
            df.columns = [col.lower().replace(' ', '_') for col in df.columns]

            if 'date' in df.columns:
                df['timestamp'] = df['date'].dt.strftime("%Y-%m-%d %H:%M:%S")

            # Rename columns to standard format
            column_mapping = {
                'last': 'close',
                'settle': 'close',
                'previous_settlement': 'prev_close'
            }
            df.rename(columns=column_mapping, inplace=True)

            # Ensure required columns exist
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            df = df[['timestamp'] + required_cols]

            print(f"Retrieved {len(df)} bars")

            return df

        except ImportError:
            print("Error: quandl not installed. Install with: pip install quandl")
            return None
        except Exception as e:
            print(f"Error fetching Quandl data: {e}")
            return None

    def load_csv(self, file_path: str):
        """
        Load data from CSV file

        Expected format: timestamp,open,high,low,close,volume

        Args:
            file_path: Path to CSV file

        Returns:
            DataFrame with OHLCV data
        """
        try:
            print(f"Loading data from {file_path}...")

            df = pd.read_csv(file_path)

            # Validate columns
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in required_cols:
                if col not in df.columns:
                    raise ValueError(f"Missing required column: {col}")

            # Ensure timestamp column
            if 'timestamp' not in df.columns:
                if 'date' in df.columns:
                    df['timestamp'] = df['date']
                elif 'datetime' in df.columns:
                    df['timestamp'] = df['datetime']
                else:
                    print("Warning: No timestamp column found. Using row index.")
                    df['timestamp'] = pd.date_range(start='2020-01-01', periods=len(df), freq='D')

            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

            print(f"Loaded {len(df)} bars")

            return df

        except Exception as e:
            print(f"Error loading CSV: {e}")
            return None

    def validate_data(self, df: pd.DataFrame) -> bool:
        """
        Validate data quality

        Args:
            df: DataFrame to validate

        Returns:
            True if data is valid
        """
        if df is None or df.empty:
            print("Validation failed: DataFrame is empty")
            return False

        # Check for required columns
        required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in df.columns:
                print(f"Validation failed: Missing column {col}")
                return False

        # Check for NaN values
        nan_count = df[required_cols[1:]].isna().sum().sum()
        if nan_count > 0:
            print(f"Warning: Found {nan_count} NaN values")

        # Check for negative prices
        price_cols = ['open', 'high', 'low', 'close']
        negative_count = (df[price_cols] < 0).sum().sum()
        if negative_count > 0:
            print(f"Warning: Found {negative_count} negative price values")

        # Check OHLC logic (high >= low, etc.)
        invalid_ohlc = ((df['high'] < df['low']) |
                       (df['high'] < df['open']) |
                       (df['high'] < df['close']) |
                       (df['low'] > df['open']) |
                       (df['low'] > df['close'])).sum()

        if invalid_ohlc > 0:
            print(f"Warning: Found {invalid_ohlc} bars with invalid OHLC relationships")

        print("Data validation complete")
        return True

    def save_data(self, df: pd.DataFrame, filename: str):
        """
        Save data to CSV

        Args:
            df: DataFrame to save
            filename: Output filename
        """
        output_file = os.path.join(self.output_path, filename)

        df.to_csv(output_file, index=False)
        print(f"Data saved to: {output_file}")

    def generate_sample_data(self, num_bars: int = 1000):
        """
        Generate sample/synthetic data for testing

        Args:
            num_bars: Number of bars to generate

        Returns:
            DataFrame with synthetic OHLCV data
        """
        print(f"Generating {num_bars} bars of synthetic data...")

        # Start with a base price and generate random walk
        base_price = 75.0
        volatility = 0.02

        dates = pd.date_range(start='2024-01-01', periods=num_bars, freq='H')
        returns = np.random.normal(0, volatility, num_bars)
        prices = base_price * np.exp(np.cumsum(returns))

        # Generate OHLC from price series
        data = []
        for i, price in enumerate(prices):
            high = price * (1 + abs(np.random.normal(0, 0.005)))
            low = price * (1 - abs(np.random.normal(0, 0.005)))
            open_price = np.random.uniform(low, high)
            close_price = np.random.uniform(low, high)

            volume = int(np.random.uniform(10000, 50000))

            data.append({
                'timestamp': dates[i].strftime("%Y-%m-%d %H:%M:%S"),
                'open': round(open_price, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'close': round(close_price, 2),
                'volume': volume
            })

        df = pd.DataFrame(data)
        print("Sample data generation complete")

        return df


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Fetch historical crude oil futures data')
    parser.add_argument('--source', type=str, choices=['yahoo', 'quandl', 'csv', 'sample'],
                       default='sample', help='Data source')
    parser.add_argument('--symbol', type=str, default='CL=F',
                       help='Symbol (for Yahoo Finance)')
    parser.add_argument('--start', type=str, default='2020-01-01',
                       help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, default=None,
                       help='End date (YYYY-MM-DD)')
    parser.add_argument('--input', type=str, default=None,
                       help='Input CSV file path (for csv source)')
    parser.add_argument('--output', type=str, default='./data',
                       help='Output directory')
    parser.add_argument('--filename', type=str, default='crude_oil_historical.csv',
                       help='Output filename')
    parser.add_argument('--api-key', type=str, default=None,
                       help='API key (for Quandl)')
    parser.add_argument('--bars', type=int, default=1000,
                       help='Number of bars for sample data')

    args = parser.parse_args()

    fetcher = CrudeOilDataFetcher(output_path=args.output)

    df = None

    if args.source == 'yahoo':
        df = fetcher.fetch_yahoo(symbol=args.symbol, start_date=args.start, end_date=args.end)
    elif args.source == 'quandl':
        if not args.api_key:
            print("Error: Quandl requires --api-key")
            return
        df = fetcher.fetch_quandl(api_key=args.api_key, start_date=args.start)
    elif args.source == 'csv':
        if not args.input:
            print("Error: CSV source requires --input file path")
            return
        df = fetcher.load_csv(args.input)
    elif args.source == 'sample':
        df = fetcher.generate_sample_data(num_bars=args.bars)

    if df is not None and fetcher.validate_data(df):
        fetcher.save_data(df, args.filename)
        print("\n" + "="*60)
        print("Data Summary:")
        print("="*60)
        print(df.describe())
        print("\nFirst 5 rows:")
        print(df.head())
        print("\nLast 5 rows:")
        print(df.tail())
    else:
        print("Data fetch/validation failed")


if __name__ == "__main__":
    main()
