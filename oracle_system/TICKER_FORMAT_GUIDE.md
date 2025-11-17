# 📋 Kalshi Ticker Format Reference

Based on Kalshi's API documentation, here's how their ticker system works:

## Structure Hierarchy

```
SERIES (Topic/Category)
  └── EVENT (Specific occurrence with date)
      └── MARKET (Binary outcome: Yes/No)
```

## Format Pattern

**Series Ticker:** `TOPIC` (e.g., `INRATE`, `BTC`, `PRES`)

**Event Ticker:** `SERIES-YYMMM` or `SERIES-YY` (e.g., `INRATE-24DEC`, `PRES-24`)

**Market Ticker:** `EVENT-OUTCOME` (e.g., `INRATE-24DEC-T4.75`, `BTC-24DEC-T100K`)

### Outcome Codes:
- `T` = "Top" or ">=" (Greater than or equal to)
- `B` = "Bottom" or "<" (Less than)
- Party names for elections: `-DEM`, `-REP`, `-IND`

## Real Examples by Category

### 🏛️ Economics

**Federal Reserve Interest Rates:**
- Series: `INRATE`
- Event: `INRATE-24DEC` (December 2024 FOMC decision)
- Markets:
  - `INRATE-24DEC-T4.75` = "Fed rate >= 4.75%"
  - `INRATE-24DEC-B4.75` = "Fed rate < 4.75%"
  - `INRATE-24DEC-T5.00` = "Fed rate >= 5.00%"

**CPI Inflation:**
- Series: `CPI`
- Event: `CPI-24NOV` (November 2024 CPI report)
- Markets:
  - `CPI-24NOV-T0.3` = "CPI MoM >= 0.3%"
  - `CPI-24NOV-B0.3` = "CPI MoM < 0.3%"

**Jobs Report:**
- Series: `JOBS` or `NFP` (Nonfarm Payrolls)
- Event: `JOBS-24NOV`
- Markets:
  - `JOBS-24NOV-T200K` = "Nonfarm payrolls >= 200K"
  - `JOBS-24NOV-B200K` = "Nonfarm payrolls < 200K"

### 🗳️ Politics

**Presidential Election:**
- Series: `PRES`
- Event: `PRES-24` or `PRES-2024`
- Markets:
  - `PRES-24-DEM` = "Democrat wins"
  - `PRES-24-REP` = "Republican wins"

**Senate Control:**
- Series: `SENATE`
- Event: `SENATE-24`
- Markets:
  - `SENATE-24-DEM` = "Democrats control Senate"
  - `SENATE-24-REP` = "Republicans control Senate"

**Approval Rating:**
- Series: `APPROVAL` or `POTUSAPP`
- Event: `APPROVAL-24DEC`
- Markets:
  - `APPROVAL-24DEC-T45` = "Approval >= 45%"

### 💰 Finance

**Bitcoin:**
- Series: `BTC` or `BTCUSD`
- Event: `BTC-24DEC` (End of December 2024)
- Markets:
  - `BTC-24DEC-T100K` = "Bitcoin >= $100,000"
  - `BTC-24DEC-T80K` = "Bitcoin >= $80,000"

**S&P 500:**
- Series: `INX` (Index)
- Event: `INX-24DEC31`
- Markets:
  - `INX-24DEC31-T5000` = "S&P 500 >= 5000"
  - `INX-24DEC31-T5500` = "S&P 500 >= 5500"

**Stock Price Ranges:**
- Series: `TESLA`, `AAPL`, etc.
- Event: `TESLA-24Q4`
- Markets:
  - `TESLA-24Q4-T200` = "Tesla >= $200/share in Q4"

## Common Abbreviations

**Time Periods:**
- `24` = 2024
- `25` = 2025
- `JAN`, `FEB`, `MAR`, `APR`, `MAY`, `JUN`
- `JUL`, `AUG`, `SEP`, `OCT`, `NOV`, `DEC`
- `Q1`, `Q2`, `Q3`, `Q4` = Quarters
- `H1`, `H2` = Half years

**Numeric Thresholds:**
- Numbers typically appear without decimals: `100K` = 100,000
- Percentages use decimals: `4.75` = 4.75%
- Basis points: `475` might mean 4.75%

**Prefixes:**
- `T` = Top/Greater than or equal
- `B` = Bottom/Less than
- `R` = Range (sometimes)

## What We Got Wrong

**Our Original Tickers (WRONG):**
```python
"FED-DEC-2024"      # ❌ Too verbose, wrong format
"BTC-100K-2024"     # ❌ Wrong date format
"CPI-NOV-2024"      # ❌ Wrong date format
"SPX-EOY-2024"      # ❌ Wrong series name
```

**Should Be (CORRECT):**
```python
"INRATE-24DEC-T4.75"    # ✅ Fed rate >= 4.75% Dec 2024
"BTC-24DEC-T100K"       # ✅ Bitcoin >= $100K Dec 2024
"CPI-24NOV-T0.3"        # ✅ CPI >= 0.3% Nov 2024
"INX-24DEC31-T5000"     # ✅ S&P >= 5000 EOY 2024
```

## How to Find Exact Tickers

You CANNOT guess these - you must discover them from the API:

### Method 1: Run Discovery Script
```bash
python3 discover_markets.py
```

This queries the API and shows you all available markets organized by category.

### Method 2: Search Kalshi Website
1. Go to https://kalshi.com
2. Browse categories (Politics, Economics, Finance)
3. Click on a market
4. Look at the URL - ticker is often visible there
5. Or inspect the page source for market data

### Method 3: Query API Directly
```python
# Get all events in a series
GET /events?series_ticker=INRATE

# Get all markets in an event
GET /markets?event_ticker=INRATE-24DEC

# Get specific market details
GET /markets/INRATE-24DEC-T4.75
```

## Pro Tips

1. **Date formats are compact:** `24DEC` not `DEC-2024`
2. **Series names are abbreviated:** `INRATE` not `FED-RATE`
3. **Thresholds use T/B:** `T100K` not `ABOVE-100K`
4. **Case sensitive:** `INRATE-24DEC` ≠ `inrate-24dec`
5. **Exact match required:** Even small differences return 404

## Next Steps

1. Run `python3 discover_markets.py` on your Mac
2. Copy the exact tickers from the output
3. Paste them into `config/markets.py`
4. Restart Oracle
5. Watch real data flow in!

**The tickers must be exact - this is why we're getting 404 errors.**
