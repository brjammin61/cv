#!/usr/bin/env python3
"""
Find active, short-term Kalshi markets with high trading volume.
"""

import requests
import json
import time
import base64
from datetime import datetime, timedelta
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
print("🎯 FINDING ACTIVE, HIGH-VOLUME MARKETS")
print("=" * 80)

# Get ALL markets (not just events)
print("\n[1] Fetching ALL ACTIVE MARKETS...")
all_markets = []
cursor = None

for page in range(5):  # Get first 5 pages (500 markets max)
    params = {'limit': 100, 'status': 'open'}
    if cursor:
        params['cursor'] = cursor

    response = make_request('GET', '/markets', params=params)

    if response and response.status_code == 200:
        data = response.json()
        markets = data.get('markets', [])
        all_markets.extend(markets)
        cursor = data.get('cursor')
        print(f"   Page {page + 1}: Found {len(markets)} markets (Total: {len(all_markets)})")

        if not cursor or len(markets) == 0:
            break
    else:
        print(f"   Failed to fetch page {page + 1}")
        break

print(f"\n✅ Total markets found: {len(all_markets)}")

# Filter for good trading markets - POLITICS & ECONOMICS ONLY
print("\n[2] Filtering for POLITICS & ECONOMICS markets with good liquidity...")

good_markets = []
politics_economics_markets = []
now = datetime.now()
six_months = now + timedelta(days=180)

# Keywords to identify politics/economics markets
politics_keywords = ['congress', 'senate', 'house', 'election', 'president', 'democrat',
                     'republican', 'vote', 'poll', 'government', 'shutdown', 'supreme',
                     'court', 'nominee', 'legislation', 'impeach', 'cabinet']
economics_keywords = ['fed', 'rate', 'inflation', 'cpi', 'gdp', 'unemployment', 'jobs',
                      'recession', 'economy', 'wage', 'interest', 'fomc', 'treasury',
                      'debt', 'deficit', 'market', 'stock', 'dow', 's&p']

for market in all_markets:
    ticker = market.get('ticker', '')
    title = market.get('title', '').lower()

    # Check if it's politics or economics related
    is_politics = any(keyword in title for keyword in politics_keywords)
    is_economics = any(keyword in title for keyword in economics_keywords)

    if not (is_politics or is_economics):
        continue  # Skip non-politics/economics markets

    # Get market details
    volume = market.get('volume', 0)
    open_interest = market.get('open_interest', 0)
    close_time = market.get('close_time', '')
    yes_bid = market.get('yes_bid', 0)
    yes_ask = market.get('yes_ask', 0)

    # Calculate spread (lower is better)
    spread = yes_ask - yes_bid if yes_ask and yes_bid else 10000

    # Store all politics/economics markets
    politics_economics_markets.append({
        'ticker': ticker,
        'title': market.get('title', ''),
        'volume': volume,
        'open_interest': open_interest,
        'spread': spread,
        'close_time': close_time,
        'yes_bid': yes_bid,
        'yes_ask': yes_ask,
        'category': 'politics' if is_politics else 'economics'
    })

    # Filter for good liquidity (relaxed criteria for politics/economics)
    if (volume > 50 or open_interest > 25) and spread < 1000:  # More lenient for behavioral markets
        good_markets.append({
            'ticker': ticker,
            'title': market.get('title', ''),
            'volume': volume,
            'open_interest': open_interest,
            'spread': spread,
            'close_time': close_time,
            'yes_bid': yes_bid,
            'yes_ask': yes_ask,
            'category': 'politics' if is_politics else 'economics'
        })

# Sort by volume
good_markets.sort(key=lambda x: x['volume'], reverse=True)

print(f"\n✅ Found {len(politics_economics_markets)} total politics/economics markets")
print(f"✅ Found {len(good_markets)} with good liquidity for trading")

# Display top markets
print("\n" + "=" * 80)
print("📊 TOP POLITICS & ECONOMICS MARKETS (by volume)")
print("=" * 80)

for i, market in enumerate(good_markets[:30], 1):
    ticker = market['ticker']
    title = market['title'][:60]
    volume = market['volume']
    spread = market['spread']
    yes_bid = market['yes_bid'] / 100  # Convert cents to probability
    yes_ask = market['yes_ask'] / 100
    category = market['category'].upper()

    print(f"\n{i}. [{category}] {ticker}")
    print(f"   {title}")
    print(f"   Volume: {volume:,} | OI: {market['open_interest']:,} | Spread: {spread} cents | Bid: {yes_bid:.2f}¢ Ask: {yes_ask:.2f}¢")

# Group by category
print("\n" + "=" * 80)
print("📂 BREAKDOWN BY CATEGORY")
print("=" * 80)

politics_markets = [m for m in good_markets if m['category'] == 'politics']
economics_markets = [m for m in good_markets if m['category'] == 'economics']

print(f"\n🏛️  POLITICS ({len(politics_markets)} markets):")
for market in politics_markets[:15]:
    print(f"  {market['ticker']:35} | Vol: {market['volume']:,} | {market['title'][:40]}")

print(f"\n💰 ECONOMICS ({len(economics_markets)} markets):")
for market in economics_markets[:15]:
    print(f"  {market['ticker']:35} | Vol: {market['volume']:,} | {market['title'][:40]}")

print("\n" + "=" * 80)
print("✅ SEARCH COMPLETE")
print("=" * 80)
print("\n💡 Use these tickers in config/markets.py for active trading!")
