# 🔍 Finding Real Kalshi Market Tickers

You're right - Kalshi has tons of politics and economics markets! The issue is we need to find the **correct ticker format** that Kalshi uses.

## Quick Fix: Run the Discovery Script

I've created a script that will query your Kalshi API and show you all available markets:

```bash
cd oracle_system
python3 discover_markets.py
```

**This will show you:**
1. All active event series organized by category (Politics, Economics, Finance, etc.)
2. Search results for specific topics (Fed, Bitcoin, Elections, etc.)
3. The actual market tickers you can use in config/markets.py

## Understanding Kalshi's Structure

Kalshi organizes markets in a hierarchy:

**EVENT SERIES** (e.g., "INRATE")
└── **EVENT** (e.g., "INRATE-24DEC")
    └── **MARKETS** (e.g., "INRATE-24DEC-T4.75", "INRATE-24DEC-B4.75")

### Ticker Format Examples:

**Fed Interest Rates:**
- Series: `INRATE` (Interest Rate)
- Event: `INRATE-24DEC` (December 2024)
- Markets: `INRATE-24DEC-T4.75` (Rate >= 4.75%), `INRATE-24DEC-B4.75` (Rate < 4.75%)

**Bitcoin:**
- Series: `BTC` or `BTCUSD`
- Event: `BTC-24DEC`
- Markets: `BTC-24DEC-T100K` (Bitcoin >= $100K by Dec 2024)

**Elections:**
- Series: `PREZ`, `SENATE`, `CONGRESS`
- Event: `PREZ-24`
- Markets: `PREZ-24-DEM`, `PREZ-24-REP`

**CPI/Inflation:**
- Series: `CPI`, `INFLATION`
- Event: `CPI-24NOV`
- Markets: `CPI-24NOV-T0.3` (CPI >= 0.3% MoM)

## What You're Looking For

After running `discover_markets.py`, look for:

### High Priority Markets (High Volume):
1. **Fed Rate Decisions** - Search for "INRATE" or "FED"
2. **Inflation/CPI** - Search for "CPI" or "INFLATION"
3. **Employment** - Search for "JOBS" or "UNEMPLOYMENT"
4. **Elections** - Search for "PREZ", "SENATE", "CONGRESS"

### Medium Priority (Good Liquidity):
5. **Bitcoin** - Search for "BTC" or "BITCOIN"
6. **Stock Market** - Search for "S&P" or "SPX"
7. **Approval Ratings** - Search for "APPROVAL"

### Fun Markets (Lower Volume):
8. **Time Person of Year** - Search for "TIME"
9. **Weather** - Search for "TEMP" or "WEATHER"

## Once You Find Real Tickers

1. Copy the real market tickers from the discovery output

2. Edit `config/markets.py`:
```bash
nano config/markets.py
```

3. Replace the example tickers with real ones:
```python
KALSHI_MARKETS = [
    # Fed Interest Rate Decision
    ("INRATE-24DEC-T4.75", "Fed Rate >= 4.75% Dec 2024"),

    # Bitcoin
    ("BTC-24DEC-T100K", "Bitcoin >= $100K by Dec 2024"),

    # Add more real tickers here
]
```

4. Restart the Oracle:
```bash
# Stop current process (Ctrl+C)
python3 run_oracle_system.py --mode paper
```

## Expected Output

Good discovery output looks like:
```
📂 ECONOMICS (15 series)
  INRATE-24DEC              | Federal Funds Rate December 2024
  CPI-24NOV                 | CPI Report November 2024
  JOBS-24NOV                | Nonfarm Payrolls November 2024

📂 POLITICS (23 series)
  PREZ-24                   | Presidential Election Winner 2024
  SENATE-24                 | Senate Control 2024
```

## Troubleshooting

**If you see "Access denied" or 403:**
- You're running from the wrong directory
- Make sure you're in `oracle_system/` folder
- API key should be loaded from config/api_keys.py

**If you see only NFL markets:**
- The default query might not include all categories
- The discovery script tries multiple search strategies
- Check the search results section for your topics

**If markets return 404:**
- The ticker format is wrong
- Use the exact tickers from the discovery output
- Kalshi tickers are case-sensitive

## Next Steps

1. **Run discovery:** `python3 discover_markets.py`
2. **Copy real tickers** from the output
3. **Update** `config/markets.py` with real tickers
4. **Restart Oracle:** `python3 run_oracle_system.py --mode paper`
5. **Watch it collect real data!**

The Oracle will then start collecting actual market data from the politics/economics markets you configure.
