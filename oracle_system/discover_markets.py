#!/usr/bin/env python3
"""
Discover available Kalshi markets and their ticker formats.

Run this on your local machine to find real market tickers.
"""

import requests
import json
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
    """Generate RSA signature for Kalshi API request."""
    message = timestamp_str + method + path
    message_bytes = message.encode('utf-8')

    signature = private_key.sign(
        message_bytes,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )

    return base64.b64encode(signature).decode('utf-8')

def make_request(method: str, path: str, params: dict = None):
    """Make an authenticated request to Kalshi API."""
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
print("🔍 KALSHI MARKET DISCOVERY")
print("=" * 80)

# Try different API endpoints to discover markets

# 1. Get all events (event series)
print("\n[1] Fetching EVENT SERIES...")
try:
    response = make_request('GET', '/events', params={'limit': 100, 'status': 'open'})

    if response.status_code == 200:
        data = response.json()
        events = data.get('events', [])
        print(f"✅ Found {len(events)} active event series\n")

        # Group by category
        by_category = {}
        for event in events:
            category = event.get('category', 'Unknown')
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(event)

        # Display by category
        for category, events_list in sorted(by_category.items()):
            print(f"\n📂 {category.upper()} ({len(events_list)} series)")
            print("-" * 80)
            for event in events_list[:5]:  # Show first 5 per category
                series_ticker = event.get('series_ticker', 'N/A')
                title = event.get('title', 'No title')
                print(f"  {series_ticker:30} | {title}")
            if len(events_list) > 5:
                print(f"  ... and {len(events_list) - 5} more")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"Response: {response.text[:500]}")

except Exception as e:
    print(f"❌ Error: {e}")


# 2. Search for specific topics
print("\n" + "=" * 80)
print("[2] Searching for SPECIFIC TOPICS...")
print("=" * 80)

search_terms = [
    'fed', 'federal reserve', 'interest rate',
    'cpi', 'inflation',
    'jobs', 'unemployment',
    'bitcoin', 'btc',
    'election', 'president', 'trump', 'biden',
    's&p', 'stock market'
]

for term in search_terms:
    try:
        response = make_request('GET', '/events', params={'limit': 10, 'status': 'open', 'search': term})

        if response and response.status_code == 200:
            data = response.json()
            events = data.get('events', [])
            if events:
                print(f"\n🔍 '{term}': Found {len(events)}")
                for event in events[:3]:
                    print(f"  → {event.get('series_ticker')}: {event.get('title', 'No title')[:60]}")
    except:
        pass


# 3. Get specific market details (try some common patterns)
print("\n" + "=" * 80)
print("[3] Testing MARKET TICKER PATTERNS...")
print("=" * 80)

# Common Kalshi ticker patterns to try
test_tickers = [
    'FED-24',
    'FEDRATE-DEC24',
    'INRATE-DEC24',
    'INXD-24',
    'CPI-24',
    'INFLATION-24',
    'BTC-24',
    'BTCUSD-24',
    'PREZ-24',
    'PRES-24'
]

print("\nTesting common ticker patterns...")
for ticker in test_tickers:
    try:
        response = make_request('GET', f'/markets/{ticker}')
        if response and response.status_code == 200:
            data = response.json()
            market = data.get('market', {})
            print(f"  ✅ {ticker}: {market.get('title', 'No title')}")
    except:
        pass


# 4. Get markets from a known event series
print("\n" + "=" * 80)
print("[4] GETTING MARKETS FROM TOP EVENTS...")
print("=" * 80)

try:
    # First get events
    response = make_request('GET', '/events', params={'limit': 20, 'status': 'open'})

    if response and response.status_code == 200:
        events = response.json().get('events', [])

        # For each event, get its markets
        for event in events[:5]:  # Check first 5 events
            series_ticker = event.get('series_ticker')
            event_ticker = event.get('event_ticker')

            if event_ticker:
                try:
                    markets_response = make_request('GET', '/markets', params={'event_ticker': event_ticker, 'limit': 10})

                    if markets_response and markets_response.status_code == 200:
                        markets = markets_response.json().get('markets', [])
                        if markets:
                            print(f"\n📊 {event.get('title', 'No title')[:60]}")
                            print(f"   Event: {event_ticker}")
                            for market in markets[:3]:
                                ticker = market.get('ticker')
                                subtitle = market.get('subtitle', 'No subtitle')
                                print(f"   → Market: {ticker}")
                                print(f"      {subtitle[:70]}")
                except:
                    pass

except Exception as e:
    print(f"❌ Error: {e}")


print("\n" + "=" * 80)
print("✅ DISCOVERY COMPLETE")
print("=" * 80)
print("\n💡 Use the tickers above to update config/markets.py")
print("   Then restart the Oracle to start collecting real data!")
