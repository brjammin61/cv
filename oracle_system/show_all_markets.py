#!/usr/bin/env python3
"""
Show ALL available Kalshi markets to understand what's actually available.
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
print("📊 ALL KALSHI MARKETS (First 100)")
print("=" * 80)

response = make_request('GET', '/markets', params={'limit': 100, 'status': 'open'})

if response and response.status_code == 200:
    data = response.json()
    markets = data.get('markets', [])

    print(f"\n✅ Found {len(markets)} markets")

    # Analyze market types
    kx_count = sum(1 for m in markets if m.get('ticker', '').startswith('KX'))
    non_kx_count = len(markets) - kx_count

    print(f"   KX markets (long-term): {kx_count}")
    print(f"   Non-KX markets: {non_kx_count}")

    # Show first 30 markets
    print("\n" + "=" * 80)
    print("FIRST 30 MARKETS:")
    print("=" * 80)

    for i, market in enumerate(markets[:30], 1):
        ticker = market.get('ticker', 'N/A')
        title = market.get('title', 'No title')[:50]
        volume = market.get('volume', 0)
        yes_bid = market.get('yes_bid', 0)
        yes_ask = market.get('yes_ask', 0)
        spread = yes_ask - yes_bid if yes_ask and yes_bid else 0

        print(f"\n{i}. {ticker}")
        print(f"   {title}")
        print(f"   Vol: {volume} | Bid: {yes_bid} | Ask: {yes_ask} | Spread: {spread}")

    # Show non-KX markets specifically
    print("\n" + "=" * 80)
    print("NON-KX MARKETS (if any):")
    print("=" * 80)

    non_kx_markets = [m for m in markets if not m.get('ticker', '').startswith('KX')]

    if non_kx_markets:
        print(f"\nFound {len(non_kx_markets)} non-KX markets in first 100:")
        for i, market in enumerate(non_kx_markets[:20], 1):
            ticker = market.get('ticker', 'N/A')
            title = market.get('title', 'No title')[:50]
            volume = market.get('volume', 0)

            print(f"{i}. {ticker:40} | Vol: {volume:6,} | {title}")
    else:
        print("\n⚠️  All markets in first 100 are KX (long-term) markets")
        print("   Kalshi may have migrated to only offering KX-style markets")
        print("   Or we need to query a different API endpoint")

    # Show volume statistics
    print("\n" + "=" * 80)
    print("VOLUME STATISTICS:")
    print("=" * 80)

    volumes = [m.get('volume', 0) for m in markets]
    if volumes:
        print(f"   Max volume: {max(volumes):,}")
        print(f"   Avg volume: {sum(volumes)/len(volumes):.0f}")
        print(f"   Markets with volume > 0: {sum(1 for v in volumes if v > 0)}")
        print(f"   Markets with volume > 100: {sum(1 for v in volumes if v > 100)}")
        print(f"   Markets with volume > 1000: {sum(1 for v in volumes if v > 1000)}")

else:
    print(f"❌ Failed to fetch markets: {response.status_code if response else 'No response'}")

print("\n" + "=" * 80)
