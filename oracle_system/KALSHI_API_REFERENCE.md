# 📚 Kalshi API Reference

Complete reference based on official Kalshi API documentation at https://docs.kalshi.com

---

## 🔐 Authentication

Kalshi uses **RSA signature-based authentication** with three custom headers.

### Required Headers

Every authenticated request requires:

```python
headers = {
    'KALSHI-ACCESS-KEY': 'your-api-key-id',           # Your API key
    'KALSHI-ACCESS-SIGNATURE': '<signature>',         # RSA signature
    'KALSHI-ACCESS-TIMESTAMP': '1703123456789',       # Timestamp in milliseconds
    'Content-Type': 'application/json'                # For POST/PUT requests
}
```

### Signature Generation

The signature is created by:

1. **Create message to sign:**
   ```
   message = timestamp + method + path
   ```

   Example: `1703123456789GET/trade-api/v2/portfolio/balance`

2. **Sign with RSA private key:**
   - Algorithm: RSA-PSS
   - Hashing: SHA-256
   - Salt length: MAX_LENGTH (PSS padding)

3. **Encode as base64:**
   ```python
   signature = base64.b64encode(signed_bytes).decode('utf-8')
   ```

### Python Implementation

```python
import time
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

# Load private key
with open('private_key.pem', 'rb') as f:
    private_key = serialization.load_pem_private_key(
        f.read(),
        password=None,
        backend=default_backend()
    )

# Generate timestamp
timestamp_ms = int(time.time() * 1000)
timestamp_str = str(timestamp_ms)

# Create message
method = 'GET'
path = '/trade-api/v2/exchange/status'
message = timestamp_str + method + path

# Sign
signature = private_key.sign(
    message.encode('utf-8'),
    padding.PSS(
        mgf=padding.MGF1(hashes.SHA256()),
        salt_length=padding.PSS.MAX_LENGTH
    ),
    hashes.SHA256()
)

# Encode
signature_b64 = base64.b64encode(signature).decode('utf-8')

# Make request
headers = {
    'KALSHI-ACCESS-KEY': api_key,
    'KALSHI-ACCESS-SIGNATURE': signature_b64,
    'KALSHI-ACCESS-TIMESTAMP': timestamp_str
}
```

---

## 🌐 API Endpoints

### Base URLs

**Production:**
```
https://api.elections.kalshi.com/trade-api/v2
```

**Demo (for testing):**
```
https://demo-api.kalshi.co/trade-api/v2
```

### Common Endpoints

#### Exchange Status
```
GET /exchange/status
```
Check if the exchange is operational.

**Response:**
```json
{
  "exchange_active": true,
  "trading_active": true
}
```

#### Get Events
```
GET /events
```

**Query Parameters:**
- `limit` (int): Number of results (1-1000, default 100)
- `status` (string): Filter by status ("open", "closed", "settled")
- `series_ticker` (string): Filter by series ticker
- `cursor` (string): Pagination cursor

**Response:**
```json
{
  "events": [
    {
      "event_ticker": "INRATE-24DEC",
      "series_ticker": "INRATE",
      "title": "Federal Funds Rate December 2024",
      "category": "Economics",
      "status": "open"
    }
  ],
  "cursor": "next_page_token"
}
```

#### Get Markets
```
GET /markets
```

**Query Parameters:**
- `limit` (int): Number of results (1-1000, default 100)
- `status` (string): Filter by status ("open", "closed", "settled")
- `event_ticker` (string): Filter by event
- `series_ticker` (string): Filter by series
- `tickers` (string): Comma-separated list of specific tickers
- `cursor` (string): Pagination cursor

**Response:**
```json
{
  "markets": [
    {
      "ticker": "INRATE-24DEC-T4.75",
      "event_ticker": "INRATE-24DEC",
      "series_ticker": "INRATE",
      "title": "Fed Rate >= 4.75% Dec 2024",
      "subtitle": "Federal Funds Rate will be 4.75% or higher",
      "yes_bid": 4500,
      "yes_ask": 4600,
      "volume": 15234,
      "status": "open"
    }
  ],
  "cursor": "next_page_token"
}
```

#### Get Specific Market
```
GET /markets/{ticker}
```

**Response:**
```json
{
  "market": {
    "ticker": "INRATE-24DEC-T4.75",
    "title": "Fed Rate >= 4.75% Dec 2024",
    "yes_bid": 4500,
    "yes_ask": 4600,
    "volume": 15234
  }
}
```

#### Get Order Book
```
GET /markets/{ticker}/orderbook
```

**Response:**
```json
{
  "yes": {
    "bids": [
      {"price": 4500, "size": 100},
      {"price": 4400, "size": 250}
    ],
    "asks": [
      {"price": 4600, "size": 75},
      {"price": 4700, "size": 150}
    ]
  },
  "no": {
    "bids": [...],
    "asks": [...]
  }
}
```

**Note:** Prices are in **cents** (4500 = $0.45 or 45%)

#### Get Portfolio
```
GET /portfolio/balance
```

**Response:**
```json
{
  "balance": 10000
}
```

#### Create Order
```
POST /portfolio/orders
```

**Request Body:**
```json
{
  "ticker": "INRATE-24DEC-T4.75",
  "client_order_id": "unique-id-12345",
  "side": "yes",
  "action": "buy",
  "count": 10,
  "type": "limit",
  "yes_price": 4500
}
```

**Response:**
```json
{
  "order": {
    "order_id": "abc123",
    "ticker": "INRATE-24DEC-T4.75",
    "status": "resting",
    "remaining_count": 10
  }
}
```

---

## 📊 Market Ticker Format

Kalshi uses a hierarchical structure:

```
SERIES → EVENT → MARKET
```

### Examples

**Federal Reserve Interest Rates:**
- Series: `INRATE`
- Event: `INRATE-24DEC` (December 2024 FOMC meeting)
- Markets:
  - `INRATE-24DEC-T4.75` = Rate >= 4.75%
  - `INRATE-24DEC-B4.75` = Rate < 4.75%
  - `INRATE-24DEC-T5.00` = Rate >= 5.00%

**Presidential Election:**
- Series: `PRES`
- Event: `PRES-2024`
- Markets:
  - `PRES-2024-DEM` = Democrat wins
  - `PRES-2024-REP` = Republican wins

**Bitcoin Price:**
- Series: `BTC`
- Event: `BTC-24DEC` (End of December 2024)
- Markets:
  - `BTC-24DEC-T100K` = Bitcoin >= $100,000
  - `BTC-24DEC-T80K` = Bitcoin >= $80,000

**Naming Convention:**
- `T` = Top/Greater than or equal (>=)
- `B` = Bottom/Less than (<)
- Dates: `24DEC` = December 2024
- Numbers: `100K` = 100,000 or `4.75` = 4.75%

---

## 💰 Pricing

All prices in the Kalshi API are in **cents**.

**Conversion:**
- API price `4500` = $0.45 = 45% probability
- API price `6200` = $0.62 = 62% probability
- API price `100` = $0.01 = 1% probability
- API price `9900` = $0.99 = 99% probability

**To convert:**
```python
# Cents to probability
probability = price_cents / 100 / 100
# Example: 4500 → 0.45 → 45%

# Probability to cents
price_cents = int(probability * 100 * 100)
# Example: 0.45 → 4500
```

---

## ⚡ WebSocket API

For real-time updates, Kalshi provides WebSocket endpoints.

**WebSocket URL:**
```
wss://api.elections.kalshi.com/trade-api/ws/v2
```

**Subscribe to market updates:**
```json
{
  "type": "subscribe",
  "channels": ["orderbook_delta"],
  "market_ticker": "INRATE-24DEC-T4.75"
}
```

---

## 🔒 Security Best Practices

### DO:
✅ Keep your private key secure and never commit to version control
✅ Use environment variables or config files (gitignored) for credentials
✅ Set file permissions to 600 on private key file
✅ Use the demo environment for testing
✅ Rotate API keys periodically

### DON'T:
❌ Share your private key or API key
❌ Commit credentials to GitHub
❌ Use production API for testing
❌ Store keys in publicly accessible locations
❌ Hardcode credentials in source code

---

## 🐛 Common Errors

### 403 Forbidden
**Cause:** Invalid signature or expired timestamp
**Fix:**
- Ensure timestamp is in milliseconds
- Verify signature algorithm (RSA-PSS with SHA256)
- Check that message = timestamp + method + path (exact format)

### 404 Not Found
**Cause:** Invalid market ticker
**Fix:** Use the exact ticker from `/events` or `/markets` endpoints

### 401 Unauthorized
**Cause:** Invalid API key
**Fix:** Verify API key matches the private key used for signing

### 400 Bad Request
**Cause:** Malformed request body or invalid parameters
**Fix:** Check request format against API documentation

---

## 📝 Rate Limits

Kalshi enforces rate limits on API requests:

- **Market Data:** Generally permissive
- **Order Placement:** Limited to prevent abuse
- **WebSocket:** Connection limits apply

**Best Practice:** Cache market data and use WebSockets for real-time updates instead of polling.

---

## 📚 Official Documentation

- **Main Docs:** https://docs.kalshi.com
- **API Reference:** https://docs.kalshi.com/api-reference
- **Quick Start:** https://docs.kalshi.com/getting_started
- **Authentication:** https://docs.kalshi.com/getting_started/quick_start_authenticated_requests
- **Market Data:** https://docs.kalshi.com/getting_started/quick_start_market_data
- **Creating Orders:** https://docs.kalshi.com/getting_started/quick_start_create_order
- **WebSockets:** https://docs.kalshi.com/getting_started/quick_start_websockets

---

## ✅ Implementation Checklist

- [ ] Download RSA private key from Kalshi account settings
- [ ] Save private key as `.pem` file with 600 permissions
- [ ] Update `KALSHI_PRIVATE_KEY_PATH` in `config/api_keys.py`
- [ ] Test authentication with `/exchange/status` endpoint
- [ ] Query available markets with `/events` and `/markets`
- [ ] Update `config/markets.py` with real market tickers
- [ ] Test order book retrieval
- [ ] Implement error handling for rate limits
- [ ] Set up WebSocket for real-time updates (optional)
- [ ] Test paper trading before live trading

---

## 🚀 Quick Start Commands

```bash
# Test authentication
python3 -c "from connectors import KalshiConnector; c = KalshiConnector(); print('Connected!' if c.connected else 'Failed')"

# Discover markets
python3 discover_markets.py

# Run Oracle in paper mode
python3 run_oracle_system.py --mode paper

# Check status
python3 status.py
```

---

**Our implementation in `connectors/kalshi_connector.py` follows this specification exactly!** ✅
