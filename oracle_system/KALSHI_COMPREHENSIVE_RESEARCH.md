# 🔬 Kalshi API & Platform: Comprehensive Research Report

**Research Date:** November 17, 2025
**Researcher:** Claude AI
**Purpose:** Become an expert on Kalshi's API, platform structure, and market access

---

## 📋 Executive Summary

This comprehensive report covers everything needed to effectively use the Kalshi prediction markets API. Key findings:

1. **Demo Environment:** Fully functional testnet with mock funds at `demo-api.kalshi.co`
2. **Authentication:** Your RSA implementation is CORRECT - Kalshi requires RSA-PSS signatures
3. **Market Access:** ALL markets (politics, economics, sports) are available through the same API
4. **Public Endpoints:** Market data can be accessed WITHOUT authentication
5. **API v2:** Current version launched in 2025, deprecated v1 as of Feb 1st, 2025

**Why You're Only Seeing KX Sports Markets:** This is likely a filtering/query issue, NOT an access restriction. All account types can access all market categories through the API.

---

## 🎮 1. Demo/Test Environment

### Demo Environment Setup

**Demo Website:** https://demo.kalshi.co
**Demo API Endpoint:** `https://demo-api.kalshi.co/trade-api/v2`

### How Demo Works

- **Mock Funds:** Yes! Demo provides virtual currency for risk-free testing
- **Separate Credentials:** Demo and production credentials are NEVER shared (security best practice)
- **Feature Parity:** All API features work identically in demo and production
- **No Real Money:** Completely safe environment for testing strategies

### Creating a Demo Account

**Step 1:** Go to https://demo.kalshi.co
**Step 2:** Sign up with:
- Fake information is ALLOWED (name, address, SSN)
- Working email address REQUIRED (for verification)
- Password you'll remember

**Step 3:** Generate Demo API Keys
- Log into demo account
- Navigate to Settings → API Keys
- Click "Create New API Key"
- Download the private key (ONE TIME ONLY!)
- Save the Key ID

**Step 4:** Test Your Setup
```python
# Point to demo environment
api_base = "https://demo-api.kalshi.co/trade-api/v2"

# Use demo credentials
api_key = "your-demo-key-id"
private_key_path = "/path/to/demo_private_key.pem"
```

### Switching Between Demo and Production

**Simple URL Change:**
```python
# Demo
demo_url = "https://demo-api.kalshi.co/trade-api/v2"

# Production
prod_url = "https://trading-api.kalshi.com/trade-api/v2"
# OR
prod_url = "https://api.elections.kalshi.com/trade-api/v2"  # Also valid!
```

**Everything else stays the same** - headers, auth, endpoints, request/response formats.

---

## 🌐 2. API Structure

### Base URLs

**Production (Live Trading):**
```
https://trading-api.kalshi.com/trade-api/v2
https://api.elections.kalshi.com/trade-api/v2  # Alternative - works for ALL markets
```

**Demo (Paper Trading):**
```
https://demo-api.kalshi.co/trade-api/v2
```

**WebSocket (Real-time):**
```
wss://trading-api.kalshi.com/trade-api/ws/v2
```

**IMPORTANT NOTE:** Despite the subdomain name "api.elections.kalshi.com", this endpoint provides access to ALL Kalshi markets - politics, economics, sports, crypto, climate, culture, etc. The "elections" subdomain is historical and does NOT indicate market restrictions.

### Market Hierarchy

Kalshi uses a three-tier structure:

```
SERIES (Topic Template)
  └── EVENT (Specific Occurrence)
      └── MARKET (Binary Yes/No Outcome)
```

**Example - Federal Reserve Interest Rates:**
- **Series:** `INRATE` (Interest Rate decisions)
- **Event:** `INRATE-24DEC` (December 2024 FOMC meeting)
- **Markets:**
  - `INRATE-24DEC-T4.75` = "Fed rate >= 4.75%"
  - `INRATE-24DEC-T5.00` = "Fed rate >= 5.00%"
  - `INRATE-24DEC-B4.75` = "Fed rate < 4.75%"

### Ticker Format Breakdown

**Series Ticker:**
- Short abbreviation: `INRATE`, `BTC`, `PRES`, `CPI`
- Represents topic category

**Event Ticker:**
- Format: `{SERIES}-{YYMM}` or `{SERIES}-{YYMMDD}`
- Examples: `INRATE-24DEC`, `BTC-24DEC31`, `PRES-24`

**Market Ticker:**
- Format: `{EVENT}-{OUTCOME}`
- Outcome codes:
  - `T` = Top/Greater than or equal (>=)
  - `B` = Bottom/Less than (<)
  - Party codes: `-DEM`, `-REP`, `-IND`
- Examples: `INRATE-24DEC-T4.75`, `BTC-24DEC-T100K`

### Available Market Categories

Kalshi offers markets across **12+ categories:**

1. **Politics** - Elections, approval ratings, legislation
2. **Economics** - Fed rates, CPI, GDP, unemployment
3. **Financials** - S&P 500, Nasdaq, individual stocks
4. **Sports** - NFL, NBA, MLB, college sports, Olympics
5. **Crypto** - Bitcoin, Ethereum price ranges
6. **Climate** - Hurricane strength, temperatures, weather events
7. **Culture** - Oscars, Grammys, Billboard charts, box office
8. **Tech & Science** - Product launches, scientific discoveries
9. **Health** - Public health metrics, disease tracking
10. **World** - International events, geopolitics
11. **Companies** - Earnings, M&A, product releases
12. **Mentions** - Media coverage, trending topics

### Key API Endpoints

#### Public Endpoints (No Auth Required)

```
GET /exchange/status
GET /markets
GET /markets/{ticker}
GET /events
GET /series
GET /markets/{ticker}/orderbook
GET /markets/{ticker}/trades
GET /markets/{ticker}/history
```

#### Authenticated Endpoints (RSA Signature Required)

```
GET /portfolio/balance
GET /portfolio/positions
GET /portfolio/orders
POST /portfolio/orders
DELETE /portfolio/orders/{order_id}
GET /portfolio/fills
GET /portfolio/settlements
```

#### Important Query Parameters

**For `/markets` endpoint:**
- `limit` (1-1000, default 100) - Results per page
- `status` (unopened, open, closed, settled) - Filter by market status
- `series_ticker` - Filter by series (e.g., `INRATE`)
- `event_ticker` - Filter by event (e.g., `INRATE-24DEC`)
- `tickers` - Comma-separated specific tickers
- `cursor` - Pagination token

**For `/series` endpoint:**
- `limit` - Results per page
- `category` - Filter by category (Politics, Economics, etc.)
- `tags` - Comma-separated tags (e.g., "Federal Reserve,Monetary Policy")

**For `/events` endpoint:**
- `status` - Filter by event status
- `series_ticker` - Filter by series
- `with_nested_markets` - Include market data in response

### Market Lifecycle & Status

Markets progress through four states:

1. **unopened** - Created but not yet tradeable
2. **open** - Active trading period
3. **closed** - Trading ended, awaiting settlement
4. **settled** - Outcome determined, payouts processed

Filter by status: `GET /markets?status=open`

---

## 🔐 3. Authentication

### Your Implementation is CORRECT! ✅

The RSA signature authentication you implemented matches Kalshi's official specification exactly.

### Authentication Requirements

**Three Custom Headers Required:**
```python
headers = {
    'KALSHI-ACCESS-KEY': 'your-api-key-id',
    'KALSHI-ACCESS-SIGNATURE': '<base64-encoded-rsa-signature>',
    'KALSHI-ACCESS-TIMESTAMP': '1731891234567',  # milliseconds
    'Content-Type': 'application/json'
}
```

### Signature Generation Process

**Step 1: Create message to sign**
```python
timestamp_ms = int(time.time() * 1000)
timestamp_str = str(timestamp_ms)
method = 'GET'  # or POST, DELETE, etc.
path = '/trade-api/v2/portfolio/balance'  # No query params!

message = timestamp_str + method + path
```

**Step 2: Sign with RSA private key**
```python
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

signature = private_key.sign(
    message.encode('utf-8'),
    padding.PSS(
        mgf=padding.MGF1(hashes.SHA256()),
        salt_length=padding.PSS.MAX_LENGTH  # Critical!
    ),
    hashes.SHA256()
)
```

**Step 3: Base64 encode**
```python
signature_b64 = base64.b64encode(signature).decode('utf-8')
```

### API Key Generation

**Production Keys:**
1. Log into https://kalshi.com
2. Profile Icon → Settings → API Keys
3. Click "Create New API Key"
4. Download private key (PEM format) - **ONE TIME ONLY**
5. Save Key ID (shown on screen)

**Demo Keys:**
1. Log into https://demo.kalshi.co
2. Same process as production
3. **Separate from production** - different credentials

### Key Security Requirements

**Private Key Format:**
- Must be PEM format
- Starts with `-----BEGIN PRIVATE KEY-----` or `-----BEGIN RSA PRIVATE KEY-----`
- Store with 600 permissions: `chmod 600 private_key.pem`
- NEVER commit to version control
- NEVER share or email

**Important Notes:**
- Private key cannot be retrieved after initial generation
- If lost, must generate new API key + private key pair
- Keys are tied together - cannot mix different key pairs
- Demo and production keys are completely separate

### Demo vs Production Keys

| Feature | Demo Keys | Production Keys |
|---------|-----------|-----------------|
| Environment | `demo-api.kalshi.co` | `trading-api.kalshi.com` |
| Real Money | No - virtual funds | Yes - real USD |
| Separate Credentials | Yes - never shared | Yes - never shared |
| Same Auth Method | RSA-PSS + SHA256 | RSA-PSS + SHA256 |
| Feature Parity | 100% same API | 100% same API |

---

## 🔍 4. Market Discovery

### Why You're Only Seeing KX Sports Markets

**The "KX" prefix is NOT sports-only!** This is a common misconception. Examples:

**KX Markets Across ALL Categories:**
- `KXINX` - S&P 500 (Financials)
- `KXBTC` - Bitcoin (Crypto)
- `KXNASDAQ100U` - Nasdaq (Financials)
- `KXMLB` - World Series (Sports)
- `KXHIGHNY` - NYC Temperature (Climate)

**Likely Causes of Only Seeing Sports:**

1. **Default Query Limitations:**
   - `/markets` without filters may prioritize high-volume markets
   - Sports currently represents 70-75% of Kalshi's trading volume
   - May appear first in paginated results

2. **Missing Category Filter:**
   ```python
   # Instead of:
   GET /markets?limit=100

   # Use:
   GET /series?category=Economics
   GET /series?category=Politics
   ```

3. **Status Filtering:**
   - Many politics/economics markets may be "settled" or "closed"
   - Default queries might only show "open" markets
   ```python
   GET /markets?status=open&series_ticker=INRATE
   ```

4. **Seasonal Availability:**
   - Election markets are seasonal (2024 vs 2025)
   - Economic data markets tied to release schedules (monthly CPI, quarterly GDP)

### How to Find Politics/Economics Markets

**Method 1: Query by Category**
```python
# Get all series in Politics category
GET /series?category=Politics

# Get all series in Economics category
GET /series?category=Economics

# Get markets for a specific series
GET /markets?series_ticker=INRATE&status=open
```

**Method 2: Search by Tags**
```python
# Tags are comma-separated
GET /series?tags=Federal Reserve,Monetary Policy
GET /series?tags=Presidential Election
GET /series?tags=Inflation,CPI
```

**Method 3: Direct Event Query**
```python
# Get events by series
GET /events?series_ticker=INRATE
GET /events?series_ticker=PRES

# Get markets for an event
GET /markets?event_ticker=INRATE-24DEC
```

**Method 4: Browse Kalshi Website**
1. Visit https://kalshi.com
2. Navigate to Politics or Economics section
3. Click on a market
4. Inspect page source or URL for ticker
5. Use exact ticker in API

### Common Series Tickers by Category

**Economics:**
- `INRATE` - Federal Funds Rate
- `CPI` - Consumer Price Index / Inflation
- `JOBS` or `NFP` - Nonfarm Payrolls
- `GDP` - Gross Domestic Product
- `UNEMP` - Unemployment Rate
- `PPI` - Producer Price Index
- `RETAIL` - Retail Sales

**Politics:**
- `PRES` - Presidential Election
- `SENATE` - Senate Control
- `HOUSE` - House Control
- `APPROVAL` or `POTUSAPP` - Presidential Approval
- `SCOTUS` - Supreme Court decisions
- `CONGRESS` - Congressional actions

**Finance:**
- `INX` or `SPX` - S&P 500
- `NASDAQ` - Nasdaq Index
- `BTC` or `BTCUSD` - Bitcoin
- `ETH` - Ethereum
- `TESLA`, `AAPL`, etc. - Individual stocks

### Using the Discovery Script

Your repository includes `discover_markets.py` - use it!

```bash
cd /home/user/cv/oracle_system
python3 discover_markets.py
```

This script:
1. Queries ALL active series
2. Groups by category
3. Shows event tickers
4. Provides searchable output

---

## 🎯 5. Market Access & Restrictions

### Account Types

Kalshi has **tiered access levels** for API usage:

**Standard Tier (Default):**
- Access to all public market data
- Standard rate limits
- Position limits: $25,000 per market
- Suitable for most traders

**Premier/Prime Tier:**
- Enhanced rate limits
- Reduced latency
- Higher position limits
- Additional features
- Requires verification of:
  - Knowledge of API security practices
  - Trading experience
  - Risk management capabilities

**Market Maker Tier:**
- Institutional access
- Custom rate limits
- Rebates/fee structures
- Direct relationship with Kalshi

### Regional Restrictions

**Kalshi is RESTRICTED in 50+ countries:**

**Blocked Regions:**
- **North America:** Canada, Cuba, Haiti, Nicaragua
- **Asia-Pacific:** Afghanistan, Australia, Laos, Myanmar, North Korea, Singapore, Taiwan, Thailand
- **South America:** Bolivia, Venezuela
- **Middle East/Africa:** Various countries under US sanctions

**Available in 130+ countries** including:
- United States (all 50 states, but see sports betting restrictions)
- United Kingdom
- European Union countries
- Most of Asia, Africa, South America

**Important:** Some US states have restrictions on sports prediction markets due to local gambling laws.

### Market-Specific Restrictions

**No category-based API restrictions exist** - all account types can access:
- Politics markets ✅
- Economics markets ✅
- Finance markets ✅
- Sports markets ✅
- All other categories ✅

**Actual restrictions are:**
1. **Geographic** - based on your location/residence
2. **Volume-based** - position limits per market
3. **Regulatory** - certain markets may be restricted in specific states
4. **Seasonal** - markets exist only when relevant (e.g., election years)

### Rate Limits

**Rate limits vary by tier and endpoint type:**

**Market Data Endpoints:**
- Generally permissive
- Designed for frequent polling
- Public endpoints have higher limits

**Trading Endpoints:**
- More restrictive
- Prevent market manipulation
- Order placement has stricter limits

**WebSocket Connections:**
- Connection limits apply
- More efficient than REST polling
- Recommended for real-time data

**Best Practice:** Use WebSockets for real-time updates, cache market data, avoid unnecessary polling.

---

## 🚀 6. Getting Started: Proper Onboarding Flow

### Recommended Setup Path

**Phase 1: Demo Environment (Week 1)**

1. **Create Demo Account**
   - Sign up at https://demo.kalshi.co
   - Use fake personal info (allowed for demo)
   - Verify email

2. **Generate Demo API Keys**
   - Settings → API Keys
   - Download private key
   - Save securely: `~/.kalshi/demo_private_key.pem`
   - Note Key ID

3. **Test Authentication**
   ```python
   # Test with demo credentials
   connector = KalshiConnector(
       api_key="demo-key-id",
       private_key_path="~/.kalshi/demo_private_key.pem",
       use_demo=True
   )

   # Verify connection
   status = connector.get_exchange_status()
   balance = connector.get_balance()  # Should show mock funds
   ```

4. **Explore Markets**
   ```bash
   # Discover available markets
   python3 discover_markets.py

   # Find politics/economics markets
   # Copy exact tickers for testing
   ```

5. **Paper Trade**
   - Place small test orders
   - Monitor order fills
   - Track P&L
   - Test your strategies

**Phase 2: Production Preparation (Week 2)**

1. **KYC Verification**
   - Complete identity verification on production site
   - Provide real information
   - Wait for approval

2. **Fund Account**
   - Start with small amount ($100-500)
   - Test deposit/withdrawal flow
   - Understand fees

3. **Generate Production Keys**
   - Separate from demo keys
   - Save: `~/.kalshi/prod_private_key.pem`
   - Set permissions: `chmod 600`

4. **Production Testing**
   - Test authentication with production API
   - Query real market data
   - DO NOT place orders yet

**Phase 3: Live Trading (Week 3+)**

1. **Small Test Trades**
   - Place minimal viable orders
   - Verify execution
   - Check fees/settlements

2. **Strategy Validation**
   - Run your Oracle in paper mode with production data
   - Verify signals match expectations
   - Monitor for 7 days minimum

3. **Gradual Scaling**
   - Start with small position sizes
   - Increase based on performance
   - Monitor risk metrics

### Complete Setup Checklist

**Demo Environment:**
- [ ] Demo account created at demo.kalshi.co
- [ ] Demo API keys generated
- [ ] Private key saved securely
- [ ] Authentication tested successfully
- [ ] Market data retrieval working
- [ ] Test orders placed and filled
- [ ] Strategies tested in paper mode

**Production Environment:**
- [ ] Production account created at kalshi.com
- [ ] KYC verification completed
- [ ] Account funded with test amount
- [ ] Production API keys generated
- [ ] Private key saved separately from demo
- [ ] Authentication tested
- [ ] Real market data verified
- [ ] Small test trade executed successfully
- [ ] 7-day validation period completed
- [ ] Risk management in place

---

## 💻 7. Code Examples & Official Resources

### Official Python SDK

**Installation:**
```bash
pip install kalshi-python
```

**Requirements:** Python 3.9+

**Basic Usage:**
```python
from kalshi_python import Configuration, KalshiClient

# Configure
config = Configuration(
    host="https://trading-api.kalshi.com/trade-api/v2"
)

# Initialize client
client = KalshiClient(
    api_key_id="your-key-id",
    private_key_path="/path/to/private_key.pem"
)

# Query markets
markets = client.markets.get_markets(limit=100, status="open")

# Get balance
balance = client.portfolio.get_balance()
```

### Official Starter Code

**Repository:** https://github.com/Kalshi/kalshi-starter-code-python

**Features:**
- RSA-PSS signature authentication implementation
- Demo and production environment support
- Example API calls
- Error handling

**Not an SDK** - designed as reference code for building your own client.

### Community Libraries

**1. AndrewNolte/KalshiPythonClient**
- OpenAPI Generator-based
- Alternative auth approach (cookie-based available)
- Comprehensive endpoint coverage

**2. humz2k/kalshi-python-unofficial**
- Lightweight wrapper
- Simple API
- Good for quick prototyping

### WebSocket Example

```python
import asyncio
import websockets
import json

async def subscribe_to_markets():
    uri = "wss://trading-api.kalshi.com/trade-api/ws/v2"

    async with websockets.connect(uri) as websocket:
        # Subscribe to orderbook
        subscription = {
            "id": 1,
            "cmd": "subscribe",
            "params": {
                "channels": ["orderbook_delta"],
                "market_tickers": ["INRATE-24DEC-T4.75"]
            }
        }

        await websocket.send(json.dumps(subscription))

        # Listen for updates
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(f"Update: {data}")

asyncio.run(subscribe_to_markets())
```

### REST API Examples

**Get Markets by Category:**
```python
import requests

# Get all Economics series
response = requests.get(
    "https://api.elections.kalshi.com/trade-api/v2/series",
    params={"category": "Economics"},
    headers={"accept": "application/json"}
)

series_list = response.json()

# Get markets for a series
for series in series_list["series"]:
    ticker = series["ticker"]

    markets_response = requests.get(
        "https://api.elections.kalshi.com/trade-api/v2/markets",
        params={
            "series_ticker": ticker,
            "status": "open",
            "limit": 100
        }
    )

    markets = markets_response.json()
    print(f"{ticker}: {len(markets['markets'])} open markets")
```

**Create Authenticated Request:**
```python
import time
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

# Load private key
with open('private_key.pem', 'rb') as f:
    private_key = serialization.load_pem_private_key(
        f.read(),
        password=None,
        backend=default_backend()
    )

# Create signature
timestamp_ms = int(time.time() * 1000)
timestamp_str = str(timestamp_ms)
method = 'GET'
path = '/trade-api/v2/portfolio/balance'
message = timestamp_str + method + path

signature = private_key.sign(
    message.encode('utf-8'),
    padding.PSS(
        mgf=padding.MGF1(hashes.SHA256()),
        salt_length=padding.PSS.MAX_LENGTH
    ),
    hashes.SHA256()
)

signature_b64 = base64.b64encode(signature).decode('utf-8')

# Make request
headers = {
    'KALSHI-ACCESS-KEY': 'your-api-key-id',
    'KALSHI-ACCESS-SIGNATURE': signature_b64,
    'KALSHI-ACCESS-TIMESTAMP': timestamp_str,
    'accept': 'application/json'
}

response = requests.get(
    f"https://api.elections.kalshi.com{path}",
    headers=headers
)

print(response.json())
```

---

## 📚 8. Official Documentation Resources

### Primary Documentation

**Main Documentation Hub:**
- https://docs.kalshi.com

**API Reference:**
- https://docs.kalshi.com/api-reference
- https://trading-api.readme.io/reference

**Getting Started Guides:**
- Quick Start (Market Data): https://docs.kalshi.com/getting_started/quick_start_market_data
- Quick Start (Authenticated): https://docs.kalshi.com/getting_started/quick_start_authenticated_requests
- Quick Start (WebSockets): https://docs.kalshi.com/getting_started/quick_start_websockets
- Demo Environment: https://docs.kalshi.com/getting_started/demo_env
- API Keys: https://docs.kalshi.com/getting_started/api_keys

**API Changelog:**
- https://docs.kalshi.com/changelog

**Python SDK:**
- https://docs.kalshi.com/python-sdk
- https://pypi.org/project/kalshi-python/

### GitHub Resources

**Official Starter Code:**
- Python: https://github.com/Kalshi/kalshi-starter-code-python
- Kalshi GitHub: https://github.com/Kalshi/

**Community Projects:**
- https://github.com/AndrewNolte/KalshiPythonClient
- https://github.com/humz2k/kalshi-python-unofficial
- https://github.com/ammario/kalshi (Go client)

### Help & Support

**Help Center:**
- https://help.kalshi.com
- https://help.kalshi.com/kalshi-api

**Discord:**
- Developer support in #dev channel
- Community discussions
- Real-time help from Kalshi team

**Direct Support:**
- support@kalshi.com
- For API issues, account problems, or technical questions

---

## 🔧 9. Troubleshooting Common Issues

### Issue: "Only seeing KX sports markets"

**Root Cause:** Query filtering, not access restriction

**Solutions:**
1. Query by category: `GET /series?category=Economics`
2. Filter by status: `GET /markets?status=open`
3. Use specific series: `GET /markets?series_ticker=INRATE`
4. Check seasonal availability (election markets only in election years)
5. Paginate through results - politics/economics might be on later pages

### Issue: "403 Forbidden" Authentication Errors

**Root Causes:**
1. Signature algorithm incorrect (must be RSA-PSS with SHA256)
2. Timestamp not in milliseconds
3. Message format wrong (should be: timestamp + method + path)
4. Query parameters included in signed message (don't include!)
5. API key doesn't match private key
6. Using demo key with production URL (or vice versa)

**Solutions:**
- Verify signature generation matches official spec
- Use `int(time.time() * 1000)` for timestamp
- Don't include query params in signed message
- Regenerate API key + private key pair together
- Check you're using correct environment URL

### Issue: "Private key not loading"

**Checks:**
1. File exists: `ls -la /path/to/private_key.pem`
2. Correct permissions: `chmod 600 private_key.pem`
3. Valid PEM format: `head -1 private_key.pem` should show `-----BEGIN PRIVATE KEY-----`
4. Path is absolute, not relative
5. No password on key (or provide password parameter)

### Issue: "No markets found for ticker"

**Root Causes:**
1. Ticker format incorrect (case-sensitive!)
2. Market has settled/closed
3. Typo in ticker
4. Market doesn't exist yet (future event)

**Solutions:**
- Use discovery script to get exact tickers
- Check market status: `GET /markets/{ticker}` returns status
- Verify ticker format: Series-Event-Outcome
- Query events first to see available markets

### Issue: "Rate limited"

**Solutions:**
- Implement exponential backoff
- Use WebSockets instead of polling
- Cache market data
- Reduce request frequency
- Consider upgrading to Premier tier if needed

---

## 🎓 10. Advanced Topics

### WebSocket Channels

**Available Channels:**
- `orderbook` - Full orderbook snapshots
- `orderbook_delta` - Incremental updates (more efficient)
- `trades` - Trade feed
- `ticker` - Market ticker updates
- `fill` - Your order fills (requires auth)

**Subscription Pattern:**
```python
{
    "id": unique_message_id,
    "cmd": "subscribe",
    "params": {
        "channels": ["orderbook_delta", "trades"],
        "market_tickers": ["INRATE-24DEC-T4.75", "BTC-24DEC-T100K"]
    }
}
```

### Multivariate Events (Combos)

**New in 2025:** Support for complex multivariate events

**Example:** "Who wins BOTH the Presidency AND Senate?"

**Endpoints:**
- `GET /events/multivariate` - Get multivariate events
- Enhanced filtering for combo markets

### Price Levels

**Important:** Prices in Kalshi API are in **CENTS**

**Conversion:**
```python
# API price to probability
probability = price_cents / 100 / 100
# Example: 4500 → 0.45 → 45%

# Probability to API price
price_cents = int(probability * 100 * 100)
# Example: 0.65 → 6500
```

**Price range:** 1-9999 (0.01% to 99.99%)

### Order Types

**Supported Order Types:**
- `limit` - Limit order at specific price
- `market` - Market order (immediate execution)

**Order Sides:**
- `yes` - Buy/sell YES contracts
- `no` - Buy/sell NO contracts

**Order Actions:**
- `buy` - Buy contracts
- `sell` - Sell contracts

### Fees & Incentives

**Trading Fees:**
- Variable by market and volume
- Check series-specific fees: `GET /series/{ticker}/fee_changes`
- Volume incentives available: `GET /incentive_programs/volume_incentives`

**Fee Types:**
- Maker fees (providing liquidity)
- Taker fees (removing liquidity)
- Settlement fees

---

## ✅ 11. Summary & Action Items

### Key Findings

1. **Your Authentication is Correct:** The RSA-PSS implementation matches Kalshi's spec perfectly
2. **Demo Environment Works:** Fully functional at `demo-api.kalshi.co` with mock funds
3. **All Markets Available:** No category-based API restrictions exist
4. **Public Endpoints:** Market data accessible without authentication
5. **KX ≠ Sports Only:** KX prefix appears across all market categories

### Why Only Sports Markets Showing

**Not an access problem!** Likely causes:
1. Default queries showing high-volume markets first (sports = 75% of volume)
2. Missing category/series filters in queries
3. Politics/economics markets may be closed/settled
4. Need to paginate through results

**Solution:** Use category filtering: `GET /series?category=Economics`

### Recommended Next Steps

**Immediate (Today):**
1. Create demo account at demo.kalshi.co
2. Generate demo API keys
3. Test authentication with demo environment
4. Run discovery script with category filters
5. Verify you can access politics/economics markets

**Short-term (This Week):**
1. Test strategies in demo environment
2. Paper trade with realistic position sizes
3. Monitor Oracle system performance
4. Validate data quality

**Medium-term (Next Week):**
1. Complete production KYC
2. Fund account with test amount
3. Generate production API keys
4. Execute small live trades

**Long-term (Month 1):**
1. Complete 7-day validation period
2. Scale up position sizes gradually
3. Implement risk management
4. Monitor and optimize

### Critical Reminders

- **Security:** Never commit private keys to version control
- **Testing:** Always test in demo before production
- **Rate Limits:** Use WebSockets for real-time data
- **Pagination:** Markets lists require pagination for complete data
- **Status Filtering:** Many markets are closed/settled - filter for "open"
- **Exact Tickers:** Market tickers are case-sensitive and must be exact

---

## 📞 12. Getting Help

**Technical Issues:**
- Discord: #dev channel for developer support
- GitHub: Check official starter code and examples
- Documentation: https://docs.kalshi.com

**Account Issues:**
- Email: support@kalshi.com
- Help Center: https://help.kalshi.com

**Emergency:**
- If API is down: Check https://status.kalshi.com (if available)
- Trading issues: Contact support immediately

---

## 📄 Appendix: Quick Reference

### Environment URLs
```
Demo:        https://demo-api.kalshi.co/trade-api/v2
Production:  https://trading-api.kalshi.com/trade-api/v2
Production:  https://api.elections.kalshi.com/trade-api/v2
WebSocket:   wss://trading-api.kalshi.com/trade-api/ws/v2
```

### Common Series Tickers
```
Economics:  INRATE, CPI, JOBS, GDP, UNEMP
Politics:   PRES, SENATE, HOUSE, APPROVAL
Finance:    INX, NASDAQ, BTC, ETH
Sports:     NFL, NBA, MLB, NCAA
Climate:    TEMP, HURRICANE, TORNADO
```

### Market Status Values
```
unopened → open → closed → settled
```

### Categories
```
Politics, Economics, Financials, Sports, Crypto,
Climate, Culture, Tech & Science, Health, World,
Companies, Mentions
```

---

**End of Comprehensive Research Report**

*This report compiled from official Kalshi documentation, API references, community resources, and real-world testing as of November 17, 2025.*
