# Kalshi API - Quick Answers to Your Questions

**Research Date:** November 17, 2025

---

## TL;DR - Critical Findings

1. **Your RSA authentication is CORRECT** - matches official spec perfectly
2. **All markets are accessible** - no category restrictions exist
3. **Demo environment works** - fully functional testnet with mock funds
4. **"KX" doesn't mean sports** - it appears across ALL market categories
5. **You're missing politics markets due to filtering** - not access restrictions

---

## 1. Demo/Test Environment

### How It Works
- **URL:** `https://demo-api.kalshi.co/trade-api/v2`
- **Website:** https://demo.kalshi.co
- **Mock Funds:** YES - completely risk-free virtual currency
- **Separate Credentials:** Demo and production NEVER share keys (security)

### Getting Demo API Keys
1. Sign up at https://demo.kalshi.co
2. Use FAKE info (allowed for demo) - just need working email
3. Settings → API Keys → Create New API Key
4. Download private key (ONE TIME ONLY!)
5. Save Key ID

### Demo vs Production
```python
# Demo
api_base = "https://demo-api.kalshi.co/trade-api/v2"

# Production (either URL works)
api_base = "https://trading-api.kalshi.com/trade-api/v2"
api_base = "https://api.elections.kalshi.com/trade-api/v2"  # Also valid!
```

Everything else identical - same API, same features, same auth method.

---

## 2. API Structure

### Base URLs

**Production:**
- `https://trading-api.kalshi.com/trade-api/v2`
- `https://api.elections.kalshi.com/trade-api/v2` (also production!)

**Demo:**
- `https://demo-api.kalshi.co/trade-api/v2`

**Important:** Despite the name "api.elections.kalshi.com", this endpoint provides access to ALL markets - politics, economics, sports, crypto, everything. The subdomain is historical.

### Market Ticker Format

```
SERIES → EVENT → MARKET

Examples:
INRATE → INRATE-24DEC → INRATE-24DEC-T4.75
BTC → BTC-24DEC → BTC-24DEC-T100K
PRES → PRES-24 → PRES-24-DEM
```

**Ticker Components:**
- `T` = Top/Greater than or equal (>=)
- `B` = Bottom/Less than (<)
- Date format: `24DEC` not `DEC-2024`

### Market Categories

**12+ categories available:**
- Politics, Economics, Financials, Sports
- Crypto, Climate, Culture, Tech & Science
- Health, World, Companies, Mentions

### Market Types

**Common series tickers:**
```
Economics:  INRATE, CPI, JOBS, GDP, UNEMP
Politics:   PRES, SENATE, HOUSE, APPROVAL
Finance:    INX, NASDAQ, BTC, ETH
Sports:     NFL, NBA, MLB, NCAA
```

---

## 3. Market Access - Why Only KX Sports?

### The Real Answer

**You're NOT restricted!** The "KX" prefix appears across ALL categories:

**KX Examples Across Categories:**
- `KXINX` - S&P 500 (Financials)
- `KXBTC` - Bitcoin (Crypto)
- `KXNASDAQ100U` - Nasdaq (Financials)
- `KXMLB` - World Series (Sports)
- `KXHIGHNY` - NYC Temperature (Climate)

### Why You're Only Seeing Sports

**Likely causes:**

1. **Volume Bias:** Sports = 75% of Kalshi's trading volume, appears first in results

2. **Missing Filters:** Default queries don't filter by category
   ```python
   # Instead of:
   GET /markets?limit=100

   # Use:
   GET /series?category=Economics
   GET /series?category=Politics
   ```

3. **Market Status:** Many politics/economics markets are closed/settled
   ```python
   # Filter for open markets only
   GET /markets?status=open&series_ticker=INRATE
   ```

4. **Seasonality:** Election markets only exist in election years

### How to Find Politics/Economics Markets

**Method 1: Query by Category**
```python
GET /series?category=Economics
GET /series?category=Politics
GET /markets?series_ticker=INRATE&status=open
```

**Method 2: Use Tags**
```python
GET /series?tags=Federal Reserve,Monetary Policy
GET /series?tags=Presidential Election
```

**Method 3: Run Discovery Script**
```bash
python3 discover_markets.py
```

### Account Types & Access

**NO category-based restrictions exist!**

All account types can access:
- Politics markets ✅
- Economics markets ✅
- Finance markets ✅
- Sports markets ✅
- All categories ✅

**Actual restrictions:**
- Geographic (50+ blocked countries)
- Volume-based (position limits)
- Regional (some US states restrict sports betting)

---

## 4. Authentication - Verified Correct!

### Your Implementation is RIGHT ✅

The RSA-PSS signature authentication in your connector matches Kalshi's official specification exactly.

### Required Headers
```python
headers = {
    'KALSHI-ACCESS-KEY': 'your-api-key-id',
    'KALSHI-ACCESS-SIGNATURE': '<base64-rsa-signature>',
    'KALSHI-ACCESS-TIMESTAMP': '1731891234567',  # milliseconds!
    'Content-Type': 'application/json'
}
```

### Signature Generation (Your Code is Correct)
```python
# 1. Create message
message = timestamp_str + method + path  # No query params!

# 2. Sign with RSA-PSS + SHA256
signature = private_key.sign(
    message.encode('utf-8'),
    padding.PSS(
        mgf=padding.MGF1(hashes.SHA256()),
        salt_length=padding.PSS.MAX_LENGTH
    ),
    hashes.SHA256()
)

# 3. Base64 encode
signature_b64 = base64.b64encode(signature).decode('utf-8')
```

### Demo vs Production Keys

**Completely Separate:**
- Demo keys → `demo-api.kalshi.co`
- Production keys → `trading-api.kalshi.com`
- NEVER shared between environments
- Must generate separately

---

## 5. Getting Started - Proper Flow

### Phase 1: Demo (Week 1)

1. Create demo account at https://demo.kalshi.co
2. Generate demo API keys
3. Test authentication
4. Run discovery script
5. Find politics/economics markets
6. Paper trade with mock funds

### Phase 2: Production Prep (Week 2)

1. Complete KYC on production site
2. Fund account with test amount ($100-500)
3. Generate production API keys (separate from demo!)
4. Test production authentication
5. Query real market data
6. DO NOT trade yet

### Phase 3: Live Trading (Week 3+)

1. Place small test trades
2. Verify execution and fees
3. Run 7-day validation
4. Gradually scale position sizes

---

## 6. Code Examples

### Query Markets by Category
```python
import requests

# Get Economics series
response = requests.get(
    "https://api.elections.kalshi.com/trade-api/v2/series",
    params={"category": "Economics"},
    headers={"accept": "application/json"}
)

# Get open markets for INRATE series
markets = requests.get(
    "https://api.elections.kalshi.com/trade-api/v2/markets",
    params={
        "series_ticker": "INRATE",
        "status": "open",
        "limit": 100
    }
)

print(markets.json())
```

### Official Python SDK
```bash
pip install kalshi-python
```

```python
from kalshi_python import Configuration, KalshiClient

client = KalshiClient(
    api_key_id="your-key-id",
    private_key_path="/path/to/private_key.pem"
)

markets = client.markets.get_markets(limit=100, status="open")
balance = client.portfolio.get_balance()
```

### WebSocket Real-time Data
```python
import asyncio
import websockets
import json

async def subscribe_to_markets():
    uri = "wss://trading-api.kalshi.com/trade-api/ws/v2"

    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({
            "id": 1,
            "cmd": "subscribe",
            "params": {
                "channels": ["orderbook_delta"],
                "market_tickers": ["INRATE-24DEC-T4.75"]
            }
        }))

        while True:
            msg = await ws.recv()
            print(json.loads(msg))
```

---

## 7. Official Resources

**Documentation:**
- Main: https://docs.kalshi.com
- API Reference: https://docs.kalshi.com/api-reference
- Quick Start: https://docs.kalshi.com/getting_started

**Code:**
- Official Starter: https://github.com/Kalshi/kalshi-starter-code-python
- Python SDK: https://pypi.org/project/kalshi-python/

**Support:**
- Discord: #dev channel
- Email: support@kalshi.com
- Help Center: https://help.kalshi.com

---

## 8. Quick Troubleshooting

**Problem: "Only seeing sports markets"**
→ Use category filter: `GET /series?category=Economics`

**Problem: "403 Forbidden"**
→ Check signature algorithm (RSA-PSS + SHA256)
→ Verify timestamp in milliseconds
→ Don't include query params in signed message

**Problem: "No markets found"**
→ Ticker format is case-sensitive
→ Check market status (may be closed/settled)
→ Use discovery script for exact tickers

**Problem: "Private key not loading"**
→ Check file exists and has 600 permissions
→ Verify PEM format: `head -1 private_key.pem`

---

## 9. Action Items

### Do This Today:

1. Create demo account: https://demo.kalshi.co
2. Generate demo API keys
3. Update config to use demo environment:
   ```python
   KALSHI_API_BASE = "https://demo-api.kalshi.co/trade-api/v2"
   ```
4. Run discovery with filters:
   ```bash
   python3 discover_markets.py
   # Look for Economics and Politics categories
   ```
5. Verify you can access non-sports markets

### Critical Findings:

- ✅ Your authentication implementation is CORRECT
- ✅ Demo environment is fully functional
- ✅ All market categories are accessible
- ✅ Public endpoints don't require auth
- ❌ Default queries show sports first (volume bias)
- 🔧 Use category filtering to find politics/economics

---

## 10. The Answer to Your Main Question

**"Why does the API only return KX sports markets?"**

**Answer:** It doesn't! This is a filtering/query issue, not an access restriction.

**The Fix:**
```python
# Instead of querying all markets (shows high-volume sports first)
GET /markets?limit=100

# Query by category
GET /series?category=Economics
GET /series?category=Politics

# Then get markets for specific series
GET /markets?series_ticker=INRATE&status=open
GET /markets?series_ticker=PRES&status=open
```

**Proof KX ≠ Sports:**
- KXINX = S&P 500 (Finance)
- KXBTC = Bitcoin (Crypto)
- KXNASDAQ100U = Nasdaq (Finance)

**Real Issue:**
- Sports markets have highest volume (75% of Kalshi)
- Default queries return high-volume markets first
- Politics/economics markets are seasonal
- Many may be closed/settled currently

**Solution:**
Use category/series filtering in your queries!

---

For complete details, see: `/home/user/cv/oracle_system/KALSHI_COMPREHENSIVE_RESEARCH.md`
