#!/usr/bin/env python3
"""
Find Kalshi markets by category - the CORRECT way.

Based on comprehensive Kalshi API research.
"""

import requests
import time
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from config.api_keys import KALSHI_API_KEY, KALSHI_API_BASE, KALSHI_PRIVATE_KEY_PATH

# Load private key
with open(KALSHI_PRIVATE_KEY_PATH, 'rb') as key_file:
    private_key = serialization.load_pem_private_key(
        key_file.read(),
        password=None,
        backend=default_backend()
    )

def generate_signature(timestamp_str: str, method: str, path: str) -> str:
    message = timestamp_str + method + path
    signature = private_key.sign(
        message.encode('utf-8'),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return base64.b64encode(signature).decode('utf-8')

def make_request(method: str, path: str, params: dict = None):
    timestamp_ms = int(time.time() * 1000)
    timestamp_str = str(timestamp_ms)
    signature = generate_signature(timestamp_str, method, path)

    headers = {
        'KALSHI-ACCESS-KEY': KALSHI_API_KEY,
        'KALSHI-ACCESS-SIGNATURE': signature,
        'KALSHI-ACCESS-TIMESTAMP': timestamp_str,
        'Content-Type': 'application/json'
    }

    url = f"{KALSHI_API_BASE}{path}"
    return requests.request(method=method, url=url, headers=headers, params=params, timeout=10)

print("=" * 80)
print("🎯 FINDING MARKETS BY CATEGORY (THE CORRECT WAY)")
print("=" * 80)

# Query by CATEGORY to find politics/economics markets
categories_to_check = [
    'Economics',
    'Politics',
    'Financials',
    'Crypto'
]

all_series = {}

for category in categories_to_check:
    print(f"\n📂 {category.upper()} MARKETS:")
    print("-" * 80)

    # Get series in this category
    response = make_request('GET', '/series', params={'category': category, 'limit': 50})

    if response and response.status_code == 200:
        data = response.json()
        series_list = data.get('series', [])

        if series_list:
            print(f"✅ Found {len(series_list)} {category} series\n")
            all_series[category] = series_list

            for i, series in enumerate(series_list[:10], 1):
                ticker = series.get('ticker', 'N/A')
                title = series.get('title', 'No title')[:50]
                frequency = series.get('frequency', 'N/A')

                print(f"{i}. {ticker:15} | {title}")

                # Get markets for this series
                markets_response = make_request('GET', '/markets',
                    params={'series_ticker': ticker, 'status': 'open', 'limit': 5})

                if markets_response and markets_response.status_code == 200:
                    markets_data = markets_response.json()
                    markets = markets_data.get('markets', [])

                    if markets:
                        for market in markets[:3]:
                            m_ticker = market.get('ticker', 'N/A')
                            m_title = market.get('subtitle', market.get('title', ''))[:60]
                            volume = market.get('volume', 0)

                            print(f"   → {m_ticker}")
                            print(f"      {m_title} (Vol: {volume:,})")
                print()

            if len(series_list) > 10:
                print(f"... and {len(series_list) - 10} more {category} series\n")
        else:
            print(f"⚠️  No {category} series found")
    else:
        status = response.status_code if response else 'No response'
        print(f"❌ Failed to fetch {category}: {status}")

# Summary
print("\n" + "=" * 80)
print("📊 SUMMARY")
print("=" * 80)

total_series = sum(len(series_list) for series_list in all_series.values())
print(f"\n✅ Total series found: {total_series}")

for category, series_list in all_series.items():
    print(f"   {category}: {len(series_list)} series")

print("\n" + "=" * 80)
print("💡 NEXT STEPS")
print("=" * 80)
print("\n1. Pick 10-15 market tickers from above")
print("2. Update config/markets.py with those tickers")
print("3. Run: python3 run_oracle_system.py --mode paper")
print("4. Start collecting real data!")
print("\n" + "=" * 80)
