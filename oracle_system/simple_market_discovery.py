#!/usr/bin/env python3
"""
Simple market discovery using direct Kalshi API calls.
No authentication required for public market data.
"""

import requests
import json

API_BASE = "https://api.elections.kalshi.com/trade-api/v2"

print("=" * 80)
print("🎯 DISCOVERING ACTIVE MARKETS ON KALSHI")
print("=" * 80)

# Fetch markets
print("\n[1] Fetching all open markets from Kalshi...")

all_markets = []
cursor = None

# Paginate through all markets
for page in range(10):  # Max 10 pages (1000 markets)
    params = {'limit': 100, 'status': 'open'}
    if cursor:
        params['cursor'] = cursor

    try:
        url = f"{API_BASE}/markets"
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            markets = data.get('markets', [])
            all_markets.extend(markets)
            cursor = data.get('cursor')

            print(f"   Page {page + 1}: Found {len(markets)} markets (Total: {len(all_markets)})")

            if not cursor or len(markets) == 0:
                break
        else:
            print(f"   ❌ Failed to fetch page {page + 1}: Status {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            break

    except Exception as e:
        print(f"   ❌ Error on page {page + 1}: {e}")
        break

print(f"\n✅ Total markets found: {len(all_markets)}")

if not all_markets:
    print("\n❌ No markets fetched. Exiting.")
    exit(1)

# Filter for politics and economics
print("\n[2] Filtering for POLITICS & ECONOMICS markets...")

politics_keywords = ['congress', 'senate', 'house', 'election', 'president', 'democrat',
                     'republican', 'vote', 'poll', 'government', 'shutdown', 'supreme',
                     'court', 'nominee', 'legislation', 'impeach', 'cabinet', 'trump',
                     'biden', 'harris', 'dc', 'federal', 'white house', 'confirmation']

economics_keywords = ['fed', 'rate', 'inflation', 'cpi', 'gdp', 'unemployment', 'jobs',
                      'recession', 'economy', 'wage', 'interest', 'fomc', 'treasury',
                      'debt', 'deficit', 'dow', 's&p', 'nasdaq', 'market', 'stock']

politics_markets = []
economics_markets = []

for market in all_markets:
    ticker = market.get('ticker', '')
    title = market.get('title', '').lower()

    # Check if politics or economics
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
        'subtitle': market.get('subtitle', ''),
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

# Display top markets
print("\n" + "=" * 80)
print("🏛️  TOP 30 POLITICS MARKETS (by volume)")
print("=" * 80)

for i, m in enumerate(politics_markets[:30], 1):
    print(f"\n{i}. {m['ticker']}")
    print(f"   {m['title'][:70]}")
    print(f"   Vol: {m['volume']:,} | OI: {m['open_interest']:,} | Spread: {m['spread']} cents")

print("\n" + "=" * 80)
print("💰 TOP 30 ECONOMICS MARKETS (by volume)")
print("=" * 80)

for i, m in enumerate(economics_markets[:30], 1):
    print(f"\n{i}. {m['ticker']}")
    print(f"   {m['title'][:70]}")
    print(f"   Vol: {m['volume']:,} | OI: {m['open_interest']:,} | Spread: {m['spread']} cents")

# Export recommended tickers
print("\n" + "=" * 80)
print("📝 RECOMMENDED TICKERS FOR CONFIG")
print("=" * 80)

print("\n🏛️  TOP 15 POLITICS TICKERS:")
for m in politics_markets[:15]:
    if m['volume'] > 100 or m['open_interest'] > 50:
        print(f"   {m['ticker']:40} # Vol: {m['volume']:,}")

print("\n💰 TOP 15 ECONOMICS TICKERS:")
for m in economics_markets[:15]:
    if m['volume'] > 100 or m['open_interest'] > 50:
        print(f"   {m['ticker']:40} # Vol: {m['volume']:,}")

print("\n" + "=" * 80)
print("✅ DISCOVERY COMPLETE")
print("=" * 80)
print(f"\nTotal politics/economics markets: {len(politics_markets) + len(economics_markets)}")
print("Use these tickers in config/markets.py!")
