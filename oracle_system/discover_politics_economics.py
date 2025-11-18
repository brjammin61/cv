#!/usr/bin/env python3
"""
Discover active politics and economics markets using the working KalshiConnector.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from connectors import KalshiConnector
import json

print("=" * 80)
print("🎯 DISCOVERING POLITICS & ECONOMICS MARKETS")
print("=" * 80)

# Initialize connector (uses public endpoints, no auth required)
print("\n[1] Initializing Kalshi connector...")
kalshi = KalshiConnector(simulate_data=False)

print("\n[2] Fetching all open markets...")

# Keywords to identify politics/economics markets
politics_keywords = ['congress', 'senate', 'house', 'election', 'president', 'democrat',
                     'republican', 'vote', 'poll', 'government', 'shutdown', 'supreme',
                     'court', 'nominee', 'legislation', 'impeach', 'cabinet', 'trump',
                     'biden', 'harris', 'dc', 'federal']
economics_keywords = ['fed', 'rate', 'inflation', 'cpi', 'gdp', 'unemployment', 'jobs',
                      'recession', 'economy', 'wage', 'interest', 'fomc', 'treasury',
                      'debt', 'deficit', 'dow', 's&p', 'nasdaq']

# Get all markets - try different approaches
all_markets = []

try:
    # Try to use the get_markets method if it exists
    if hasattr(kalshi, 'get_markets'):
        print("   Using get_markets() method...")
        markets = kalshi.get_markets(status='open', limit=200)
        if markets:
            all_markets = markets
            print(f"   ✅ Found {len(all_markets)} open markets")
    else:
        print("   ⚠️  get_markets() not available, trying alternative...")
        # Try to fetch market data directly
        # This is what the connector might be using internally
        import requests
        url = "https://api.elections.kalshi.com/trade-api/v2/markets?limit=200&status=open"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            all_markets = data.get('markets', [])
            print(f"   ✅ Found {len(all_markets)} open markets via direct API call")
        else:
            print(f"   ❌ API call failed: {response.status_code}")

except Exception as e:
    print(f"   ❌ Error fetching markets: {e}")
    print("\n   Trying direct requests approach...")
    import requests
    try:
        url = "https://api.elections.kalshi.com/trade-api/v2/markets?limit=200&status=open"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            all_markets = data.get('markets', [])
            print(f"   ✅ Found {len(all_markets)} open markets")
    except Exception as e2:
        print(f"   ❌ Direct request also failed: {e2}")

if not all_markets:
    print("\n❌ Could not fetch markets. Exiting.")
    sys.exit(1)

print(f"\n[3] Filtering for politics & economics markets...")

politics_markets = []
economics_markets = []

for market in all_markets:
    ticker = market.get('ticker', '')
    title = market.get('title', '').lower()

    # Check if it's politics or economics related
    is_politics = any(keyword in title for keyword in politics_keywords)
    is_economics = any(keyword in title for keyword in economics_keywords)

    if not (is_politics or is_economics):
        continue

    volume = market.get('volume', 0)
    open_interest = market.get('open_interest', 0)
    yes_bid = market.get('yes_bid', 0)
    yes_ask = market.get('yes_ask', 0)
    spread = yes_ask - yes_bid if yes_ask and yes_bid else 10000

    market_info = {
        'ticker': ticker,
        'title': market.get('title', ''),
        'volume': volume,
        'open_interest': open_interest,
        'spread': spread,
        'yes_bid': yes_bid,
        'yes_ask': yes_ask,
        'close_time': market.get('close_time', ''),
        'category': 'politics' if is_politics else 'economics'
    }

    if is_politics:
        politics_markets.append(market_info)
    else:
        economics_markets.append(market_info)

# Sort by volume
politics_markets.sort(key=lambda x: x['volume'], reverse=True)
economics_markets.sort(key=lambda x: x['volume'], reverse=True)

print(f"✅ Found {len(politics_markets)} politics markets")
print(f"✅ Found {len(economics_markets)} economics markets")

# Display results
print("\n" + "=" * 80)
print("🏛️  POLITICS MARKETS (sorted by volume)")
print("=" * 80)

for i, market in enumerate(politics_markets[:20], 1):
    ticker = market['ticker']
    title = market['title'][:65]
    volume = market['volume']
    oi = market['open_interest']
    spread = market['spread']

    print(f"\n{i}. {ticker}")
    print(f"   {title}")
    print(f"   Vol: {volume:,} | OI: {oi:,} | Spread: {spread} cents")

print("\n" + "=" * 80)
print("💰 ECONOMICS MARKETS (sorted by volume)")
print("=" * 80)

for i, market in enumerate(economics_markets[:20], 1):
    ticker = market['ticker']
    title = market['title'][:65]
    volume = market['volume']
    oi = market['open_interest']
    spread = market['spread']

    print(f"\n{i}. {ticker}")
    print(f"   {title}")
    print(f"   Vol: {volume:,} | OI: {oi:,} | Spread: {spread} cents")

# Print recommended tickers for config
print("\n" + "=" * 80)
print("📝 RECOMMENDED TICKERS FOR CONFIG/MARKETS.PY")
print("=" * 80)

print("\n🏛️  TOP 10 POLITICS (high volume):")
for market in politics_markets[:10]:
    print(f"   {market['ticker']:40} # {market['title'][:50]}")

print("\n💰 TOP 10 ECONOMICS (high volume):")
for market in economics_markets[:10]:
    print(f"   {market['ticker']:40} # {market['title'][:50]}")

print("\n" + "=" * 80)
print("✅ DISCOVERY COMPLETE")
print("=" * 80)
print(f"\nTotal markets found: {len(politics_markets) + len(economics_markets)}")
print("Use these tickers to replace the placeholders in config/markets.py!")
