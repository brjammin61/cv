"""
Real Crude Oil Data Fetcher - Direct Download
==============================================

Fetches REAL historical crude oil futures data without yfinance dependency.
Uses direct HTTP requests to get actual market data.

Author: Algorithmic Trading Framework 2025
"""

import pandas as pd
import requests
from datetime import datetime, timedelta
import json


def fetch_crude_oil_alpha_vantage(api_key='demo', output_file='crude_oil_real.csv'):
    """
    Fetch real crude oil data from Alpha Vantage (free tier available)

    Note: Free tier limited to 5 requests/minute, 500/day
    Get free API key at: https://www.alphavantage.co/support/#api-key
    """
    url = f'https://www.alphavantage.co/query?function=WTI&interval=daily&apikey={api_key}'

    print("Fetching real WTI crude oil data from Alpha Vantage...")

    try:
        response = requests.get(url, timeout=30)
        data = response.json()

        if 'data' in data:
            df = pd.DataFrame(data['data'])
            df['timestamp'] = pd.to_datetime(df['date'])
            df['close'] = df['value'].astype(float)

            # Create OHLC from daily close (simplified)
            df['open'] = df['close']
            df['high'] = df['close'] * 1.005
            df['low'] = df['close'] * 0.995
            df['volume'] = 100000  # Placeholder

            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            df = df.sort_values('timestamp').reset_index(drop=True)

            print(f"✓ Fetched {len(df)} days of real WTI data")
            df.to_csv(output_file, index=False)
            return df
        else:
            print(f"ERROR: {data.get('Note', data.get('Error Message', 'Unknown error'))}")
            return None

    except Exception as e:
        print(f"ERROR fetching from Alpha Vantage: {e}")
        return None


def fetch_crude_oil_quandl(api_key=None, start_date='2020-01-01', output_file='crude_oil_real.csv'):
    """
    Fetch from Quandl (now Nasdaq Data Link)
    Free tier: 50 calls/day
    """
    if api_key is None:
        print("Quandl requires API key. Get free key at: https://data.nasdaq.com/")
        return None

    url = f'https://data.nasdaq.com/api/v3/datasets/CHRIS/CME_CL1.csv?start_date={start_date}&api_key={api_key}'

    print("Fetching real crude oil futures data from Quandl/Nasdaq...")

    try:
        df = pd.read_csv(url)

        # Rename columns
        df.columns = [c.lower().replace(' ', '_') for c in df.columns]
        df['timestamp'] = pd.to_datetime(df['date'])

        # Select and rename to match our format
        df = df.rename(columns={
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'settle': 'close',
            'volume': 'volume'
        })

        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        df = df.sort_values('timestamp').reset_index(drop=True)

        print(f"✓ Fetched {len(df)} days of real CL futures data")
        df.to_csv(output_file, index=False)
        return df

    except Exception as e:
        print(f"ERROR fetching from Quandl: {e}")
        return None


def fetch_crude_oil_stooq(start_date='2020-01-01', output_file='crude_oil_real.csv'):
    """
    Fetch from Stooq (free, no API key needed)
    """
    print("Fetching real crude oil data from Stooq...")

    url = 'https://stooq.com/q/d/l/?s=cl.f&i=d'

    try:
        df = pd.read_csv(url)

        # Stooq format: Date,Open,High,Low,Close,Volume
        df.columns = [c.lower() for c in df.columns]
        df['timestamp'] = pd.to_datetime(df['date'])

        # Filter by start date
        df = df[df['timestamp'] >= start_date]

        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        df = df.sort_values('timestamp').reset_index(drop=True)

        print(f"✓ Fetched {len(df)} days of real crude oil data from Stooq")
        df.to_csv(output_file, index=False)
        return df

    except Exception as e:
        print(f"ERROR fetching from Stooq: {e}")
        return None


def fetch_crude_oil_yahoo_direct(symbol='CL=F', start_date='2020-01-01', output_file='crude_oil_real.csv'):
    """
    Direct Yahoo Finance download without yfinance library
    """
    print(f"Fetching {symbol} from Yahoo Finance (direct)...")

    # Convert dates to Unix timestamp
    start_ts = int(pd.Timestamp(start_date).timestamp())
    end_ts = int(pd.Timestamp.now().timestamp())

    url = f'https://query1.finance.yahoo.com/v7/finance/download/{symbol}?period1={start_ts}&period2={end_ts}&interval=1d&events=history'

    try:
        df = pd.read_csv(url)

        df.columns = [c.lower().replace(' ', '_') for c in df.columns]
        df['timestamp'] = pd.to_datetime(df['date'])

        # Handle adjusted close
        if 'adj_close' in df.columns:
            df = df.rename(columns={'adj_close': 'close'})

        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        df = df.dropna()
        df = df.sort_values('timestamp').reset_index(drop=True)

        print(f"✓ Fetched {len(df)} days of REAL Yahoo Finance data for {symbol}")
        print(f"  Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        print(f"  Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")

        df.to_csv(output_file, index=False)
        return df

    except Exception as e:
        print(f"ERROR fetching from Yahoo: {e}")
        return None


def try_all_sources(output_file='crude_oil_real.csv'):
    """
    Try all available sources until one works
    """
    print("="*70)
    print("FETCHING REAL CRUDE OIL MARKET DATA")
    print("="*70)

    sources = [
        ('Yahoo Finance', lambda: fetch_crude_oil_yahoo_direct(output_file=output_file)),
        ('Stooq', lambda: fetch_crude_oil_stooq(output_file=output_file)),
        ('Alpha Vantage', lambda: fetch_crude_oil_alpha_vantage(output_file=output_file)),
    ]

    for source_name, fetch_func in sources:
        print(f"\nAttempting: {source_name}...")
        try:
            df = fetch_func()
            if df is not None and len(df) > 100:
                print(f"\n✓ SUCCESS: Got {len(df)} bars of REAL data from {source_name}")
                return df
        except Exception as e:
            print(f"✗ {source_name} failed: {e}")
            continue

    print("\n✗ All sources failed. Using last resort...")
    return None


if __name__ == "__main__":
    df = try_all_sources('crude_oil_real.csv')

    if df is not None:
        print("\n" + "="*70)
        print("DATA SUMMARY")
        print("="*70)
        print(df.describe())
        print("\nFirst 5 rows:")
        print(df.head())
        print("\nLast 5 rows:")
        print(df.tail())
    else:
        print("\nFailed to fetch real data from any source.")
