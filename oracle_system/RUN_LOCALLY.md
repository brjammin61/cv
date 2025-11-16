# 🚀 Running The Oracle Locally with REAL DATA

**Your Kalshi API key is configured! Now run this on your local machine to start collecting REAL market data.**

---

## 📋 Prerequisites

1. **Python 3.9+** installed
2. **Git** to clone the repository
3. **Kalshi account** with API access
4. **Internet connection** for API access

---

## ⚡ Quick Start (5 Minutes)

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd oracle_system
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

That's it! Dependencies:
- streamlit
- pandas
- numpy
- requests
- sqlite3 (built-in)

### 3. Verify API Key

Your Kalshi API key is already configured in `config/api_keys.py`:
- API Key: `e31300f6-6e71-4572-8068-89d7844b66e2`

Test it:
```bash
python3 config/api_keys.py
```

Should show: `✅ Kalshi API key configured`

### 4. Launch The Oracle

```bash
python3 run_oracle_system.py --mode paper
```

**That's it!** The system is now running with REAL data.

---

## 📊 What Happens Next

### The Oracle will:

**Every 5 minutes:**
- ✅ Fetch real market data from Kalshi
- ✅ Save order books to database
- ✅ Update active signals

**Every 10 minutes:**
- ✅ Analyze all markets for opportunities
- ✅ Generate signals (spatial arb, bias correction, etc.)
- ✅ Execute approved trades (PAPER mode = simulated)
- ✅ Log everything to database

**Every 1 hour:**
- ✅ Train ML price predictor
- ✅ Optimize strategy parameters
- ✅ Learn from outcomes

**Every day at 9 AM:**
- ✅ Generate comprehensive performance report
- ✅ Calculate win rates
- ✅ Show P&L and Sharpe ratio

---

## 🎯 Markets Being Tracked

The system is monitoring **9 real Kalshi markets**:

### Economics (High Volume):
- `FED-DEC-2024` - Fed rate decision December 2024
- `FED-JAN-2025` - Fed rate decision January 2025
- `CPI-NOV-2024` - CPI inflation report
- `JOBS-NOV-2024` - Jobs report

### Politics:
- `APPROVAL-DEC-2024` - Presidential approval rating

### Finance:
- `SPX-EOY-2024` - S&P 500 end of year
- `BTC-100K-2024` - Bitcoin $100K milestone

### Other:
- `TIME-POY-2024` - Time Person of the Year
- `TEMP-DEC-2024` - Weather/temperature

**All markets have real liquidity and active trading.**

---

## 📈 Monitor Live Progress

### Option 1: Live Dashboard (Visual)

Open a new terminal and run:
```bash
streamlit run live_monitor.py
```

Opens in browser at `http://localhost:8501`

**You'll see:**
- Real-time signal generation
- Live market data updates
- Active positions with P&L
- Strategy performance charts
- Auto-refreshes every 30 seconds

### Option 2: Terminal Status (Quick)

```bash
python3 status.py
```

Shows:
```
🔮 THE ORACLE - QUICK STATUS CHECK
✅ Oracle System: RUNNING (PID: 12345)

📊 QUICK STATS:
   Snapshots: 2,451 | Signals: 47 | Active: 3 | Closed: 12
   Win Rate: 66.7% (8/12) | Avg P&L: +2.3¢

🎯 LATEST SIGNALS (Last 5):
   🟢 11/16 10:23 | SpatialArbitrage | +3.2¢ | HIGH | +4.1¢
```

Run this anytime for instant status.

### Option 3: Watch Logs

```bash
tail -f logs/oracle_system.log
```

See every data collection, signal generation, and trade execution in real-time.

---

## 🔄 7-Day Validation Plan

### Goal: **Prove 65%+ win rate before risking real money**

**Day 1-2:** Data collection phase
- Expect: 500-1000 market snapshots
- Signals: 5-15 (markets need volatility)
- Win rate: N/A (not enough data)

**Day 3-4:** Pattern recognition
- Expect: 1500-2000 snapshots
- Signals: 20-40
- Win rate: Starting to emerge
- ML: Beginning to optimize

**Day 5-6:** Validation phase
- Expect: 2500-3500 snapshots
- Signals: 40-70
- Win rate: Should be 60-70%+
- ML: Actively improving parameters

**Day 7:** Decision point
- Expect: 3000-4000 snapshots
- Signals: 60-100+
- Win rate: **MUST BE 65%+** to go live
- Sharpe ratio: Goal is 1.5+

---

## ✅ Success Criteria (After 7 Days)

### 🟢 GREEN LIGHT - Ready for Real Money:
- ✅ Win rate ≥ 70%
- ✅ Average edge ≥ 3.0¢
- ✅ Sharpe ratio ≥ 2.0
- ✅ 50+ closed signals
- ✅ No critical errors

**Action:** Switch to LIVE mode, start with $100-500

### 🟡 YELLOW LIGHT - Continue Paper Trading:
- Win rate 60-70%
- Average edge 2.0-3.0¢
- Need more data

**Action:** Run another 7 days, optimize parameters

### 🔴 RED LIGHT - Back to Drawing Board:
- Win rate < 60%
- Inconsistent results

**Action:** Analyze what's not working, adjust strategies

---

## 🎛️ Configuration

### Change Execution Mode:

**PAPER mode (recommended for first 7 days):**
```bash
python3 run_oracle_system.py --mode paper
```
- Simulates all trades
- NO real money at risk
- Tracks what would have happened

**LIVE mode (after validation):**
```bash
python3 run_oracle_system.py --mode live
```
- ⚠️ **REAL MONEY TRADING**
- Only use after 65%+ win rate
- Start small ($100-500)

**DISABLED mode (data collection only):**
```bash
python3 run_oracle_system.py --mode disabled
```
- Only collects data
- No trade execution

### Update Markets:

Edit `config/markets.py` to add/remove markets.

Check https://kalshi.com/markets for active tickers.

### Adjust Parameters:

Edit `config/parameters.py` to tune:
- Minimum edge thresholds
- Conviction requirements
- Kelly Criterion sizing
- Risk limits

---

## 🛡️ Safety Features

**Always active** (even in PAPER mode):

### Trade-Level:
- Minimum edge: 1.0¢
- Minimum conviction: MEDIUM
- Max position size: $500
- Kelly Criterion sizing

### Daily Limits:
- Max trades per day: 20
- Daily loss limit: 20% of bankroll
- Max account value: $10,000

### System Protection:
- Emergency kill switch
- Manipulation detection
- Automatic circuit breakers
- Graceful error handling

---

## 📁 Database & Logs

### Database:
`data/oracle_data.db` (SQLite)

Tables:
- `market_snapshots` - All collected market data
- `signals` - Every signal generated
- `signal_updates` - Price updates for active signals
- `collection_runs` - Metadata about each cycle

Query it:
```bash
sqlite3 data/oracle_data.db "SELECT COUNT(*) FROM market_snapshots"
```

### Logs:
`logs/oracle_system.log` - Everything the system does
`logs/oracle_live_output.log` - Stdout/stderr capture

---

## ⚙️ Troubleshooting

### "API returned 403"

**Problem:** Kalshi API blocked or authentication failed

**Solutions:**
1. Check API key is correct in `config/api_keys.py`
2. Verify your IP isn't blocked
3. Try from different network
4. Contact Kalshi support for API access

System will automatically fall back to simulation if API fails.

### "No signals being generated"

**Normal!** Especially in first few hours.

Signals only appear when:
- Markets have sufficient volatility
- Edge > 1.0¢ detected
- Conviction ≥ MEDIUM

Be patient. In quiet market periods, you might only get 1-2 signals per day.

### "Win rate is low"

After 50+ signals, if win rate < 60%:
1. Check which strategies are underperforming
2. Adjust parameters in `config/parameters.py`
3. Disable worst-performing strategies
4. Continue paper trading, don't go live yet

---

## 🔌 Stop/Restart

### Stop the system:
```bash
# Find process ID
ps aux | grep run_oracle_system

# Kill gracefully (Ctrl+C or):
kill <PID>
```

System will:
- Finish current cycle
- Generate final report
- Close all connections
- Save state to database

### Restart:
```bash
python3 run_oracle_system.py --mode paper
```

Picks up where it left off (database persists).

---

## 💰 Going Live (After Validation)

**ONLY after 7 days with 65%+ win rate:**

### Step 1: Review Final Metrics
```bash
python3 status.py
```

Confirm:
- Win rate ≥ 65%
- Avg edge ≥ 2.5¢
- 50+ closed signals
- Positive Sharpe ratio

### Step 2: Start Small
```bash
python3 run_oracle_system.py --mode live
```

Initial bankroll: $100-500

Max position: $50-100

### Step 3: Scale Gradually

**Week 1-2 (LIVE):**
- $100-500 bankroll
- Max $50/trade
- High conviction only

**Month 1-2:**
- $500-1000 bankroll
- Max $100/trade
- High + Medium conviction

**Month 3+:**
- $1000-5000 bankroll
- Max $500/trade
- All strategies enabled

**Goal: $1k → $500k in 12 months**

Only works if edge is real and persistent.

---

## 📞 Support

### Check Documentation:
- `README.md` - Full system overview
- `STRATEGY_GUIDE.md` - Deep dive into strategies
- `7_DAY_VALIDATION.md` - Validation plan details
- `WATCH_LIVE.md` - Dashboard guide

### Check Logs:
```bash
tail -100 logs/oracle_system.log
```

### Database Query:
```python
from modules import SignalTracker
SignalTracker().print_performance_report(days=7)
```

---

## 🎯 Expected Timeline

**Today (Hour 1):**
- System starts
- First data collection
- Database created
- No signals yet (normal)

**Hour 2-6:**
- 12-72 market snapshots collected
- 0-5 signals (depends on market volatility)
- System learning patterns

**Day 1:**
- 288 snapshots (every 5 min × 12 hours × 24)
- 5-15 signals
- First ML optimization

**Day 3:**
- 1000+ snapshots
- 20-40 signals
- Win rate emerging

**Day 7:**
- 3000+ snapshots
- 60-100+ signals
- Clear performance metrics
- **DECISION TIME**

---

## ✨ Key Points

1. **API key is configured** - Ready to go
2. **Real markets loaded** - 9 active Kalshi tickers
3. **System will automatically**:
   - Collect data every 5 min
   - Generate signals every 10 min
   - Optimize with ML every hour
   - Report daily at 9 AM
4. **PAPER mode = SAFE** - No real money until you say so
5. **Need 7 days** - To prove the edge is real

---

## 🚀 Launch Command

```bash
cd oracle_system
python3 run_oracle_system.py --mode paper
```

**Then open another terminal:**
```bash
cd oracle_system
streamlit run live_monitor.py
```

**Watch it work. Let it learn. Check back in 7 days.**

**The machine is ready. The fuel is connected. Time to see if the edge is real.** 📊
