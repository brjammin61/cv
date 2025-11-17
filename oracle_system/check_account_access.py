#!/usr/bin/env python3
"""
Check what the API key has access to by querying account endpoints.
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
print("🔍 CHECKING API KEY ACCESS & ACCOUNT INFO")
print("=" * 80)

# 1. Get balance
print("\n[1] Portfolio Balance:")
response = make_request('GET', '/portfolio/balance')
if response and response.status_code == 200:
    data = response.json()
    balance = data.get('balance', 0) / 100  # Convert cents to dollars
    print(f"   ✅ Balance: ${balance:.2f}")
else:
    print(f"   ❌ Failed: {response.status_code if response else 'No response'}")

# 2. Get portfolio/positions
print("\n[2] Current Positions:")
response = make_request('GET', '/portfolio/positions')
if response and response.status_code == 200:
    data = response.json()
    positions = data.get('positions', [])
    print(f"   ✅ Active positions: {len(positions)}")
    for pos in positions[:5]:
        print(f"      - {pos.get('ticker')}: {pos.get('position')}")
else:
    print(f"   ❌ Failed: {response.status_code if response else 'No response'}")

# 3. Check exchange status
print("\n[3] Exchange Status:")
response = make_request('GET', '/exchange/status')
if response and response.status_code == 200:
    data = response.json()
    print(f"   ✅ Exchange Active: {data.get('exchange_active')}")
    print(f"   ✅ Trading Active: {data.get('trading_active')}")
else:
    print(f"   ❌ Failed: {response.status_code if response else 'No response'}")

# 4. Try different market queries
print("\n[4] Testing Different Market Queries:")

queries = [
    ('All markets', {'limit': 10, 'status': 'open'}),
    ('Series: INRATE', {'series_ticker': 'INRATE', 'limit': 10}),
    ('Series: FED', {'series_ticker': 'FED', 'limit': 10}),
    ('Series: PRES', {'series_ticker': 'PRES', 'limit': 10}),
    ('Non-KX only', {'limit': 100}),  # We'll filter after
]

for name, params in queries:
    response = make_request('GET', '/markets', params=params)
    if response and response.status_code == 200:
        data = response.json()
        markets = data.get('markets', [])

        if name == 'Non-KX only':
            markets = [m for m in markets if not m.get('ticker', '').startswith('KX')]
            print(f"   {name}: {len(markets)} markets found")
            if markets:
                for m in markets[:3]:
                    print(f"      → {m.get('ticker')}")
        else:
            print(f"   {name}: {len(markets)} markets")
            if markets:
                for m in markets[:3]:
                    print(f"      → {m.get('ticker')}")
    else:
        print(f"   {name}: Failed ({response.status_code if response else 'No response'})")

# 5. Check what categories exist
print("\n[5] API Base URL Check:")
print(f"   Using: {KALSHI_API_BASE}")
print(f"   API Key (first 20 chars): {KALSHI_API_KEY[:20]}...")

# 6. Try the main API (not elections subdomain)
print("\n[6] Trying Main API Endpoint:")
alt_base = "https://trading-api.kalshi.com/trade-api/v2"
print(f"   Testing: {alt_base}")

# Just test exchange status
timestamp_ms = int(time.time() * 1000)
timestamp_str = str(timestamp_ms)
signature = generate_signature(timestamp_str, 'GET', '/exchange/status')

headers = {
    'KALSHI-ACCESS-KEY': KALSHI_API_KEY,
    'KALSHI-ACCESS-SIGNATURE': signature,
    'KALSHI-ACCESS-TIMESTAMP': timestamp_str,
    'Content-Type': 'application/json'
}

try:
    response = requests.get(f"{alt_base}/exchange/status", headers=headers, timeout=10)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("   ✅ Main API works! Might need to use this endpoint instead")
    else:
        print(f"   Response: {response.text[:200]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 80)
print("💡 RECOMMENDATIONS:")
print("=" * 80)
print("\nBased on the results:")
print("1. If balance/positions work → API key is valid")
print("2. If only KX markets appear → May need different API tier/access")
print("3. If main API works → Update KALSHI_API_BASE in config")
print("4. Contact Kalshi support to ask about accessing politics/economics markets")
print("=" * 80)
