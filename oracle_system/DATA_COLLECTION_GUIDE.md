# 📊 Data Collection System - Launch Guide

**24/7 Real-Time Market Data Collection & Signal Tracking**

## 🎯 What This Does

The data collection system runs 24/7 and automatically:

1. **Collects market data** from Kalshi & Polymarket every 5 minutes
2. **Generates signals** using all 5 Oracle strategies every 10 minutes
3. **Tracks signal performance** in real-time
4. **Builds historical database** for backtesting
5. **Validates strategies** on REAL data (no money at risk)

**After 1 week, you'll have:**
- 2,000+ real market snapshots
- 50-100+ logged signals
- Actual win rates on live data
- Performance validation
- Backtest-ready database

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Install Dependencies

```bash
cd oracle_system
source venv/bin/activate  # If not already activated
```

### Step 2: Launch Data Collection

```bash
python run_data_collection.py
```

You'll see:
```
================================================================================
THE ORACLE - 24/7 Data Collection & Signal Tracking
================================================================================

Starting 24/7 data collection system
Data collection interval: 300s (5.0 min)
Signal generation interval: 600s (10.0 min)
Press Ctrl+C to stop gracefully

================================================================================
DATA COLLECTION CYCLE #1
================================================================================
```

### Step 3: Let It Run

The system will now run continuously. You can:

**Option A: Run in Foreground** (see live output)
- Just leave the terminal open
- Press `Ctrl+C` to stop gracefully

**Option B: Run in Background** (recommended for 24/7)
```bash
nohup python run_data_collection.py > logs/collection_output.log 2>&1 &

# To check if it's running:
ps aux | grep run_data_collection

# To stop it:
kill <process_id>
```

---

## 📊 What's Being Collected

### Market Snapshots Table

Every 5 minutes, for each market:
- Exchange (kalshi/polymarket)
- Best Bid / Best Ask
- Mid Price
- Spread
- Volume
- Timestamp

### Signals Table

Every 10 minutes, when signals detected:
- Strategy used
- Market name
- Signal type (BUY, SELL, etc.)
- Edge calculated (cents)
- Conviction level
- Entry price
- Current price (updated automatically)
- Profit/Loss (calculated in real-time)

---

## 📈 Monitoring Performance

### Check Signal Performance (Any Time)

```python
from modules import SignalTracker

tracker = SignalTracker()
tracker.print_performance_report(days=7)
```

Output:
```
================================================================================
SIGNAL TRACKER PERFORMANCE REPORT (Last 7 days)
================================================================================

📊 Total Signals: 47

🎯 By Conviction:
  HIGH: 12 (25.5%)
  MEDIUM: 25 (53.2%)
  LOW: 10 (21.3%)

✅ Closed Signals: 15
  Wins: 11
  Losses: 4
  Win Rate: 73.3%

💰 P&L:
  Total: +18.50¢
  Avg per signal: +1.23¢

📈 Edge:
  Average: +2.8¢
  Absolute: 3.2¢
```

### Check Data Collection Stats

```python
from modules import DataCollector

collector = DataCollector()
stats = collector.get_statistics()
print(f"Total snapshots: {stats['total_snapshots']}")
print(f"By exchange: {stats['by_exchange']}")
```

---

## 🔍 Running Backtests

After collecting 7+ days of data:

```python
from modules import Backtester

backtester = Backtester()

# Run backtests on all strategies
results = backtester.backtest_all_strategies(days=7, min_edge=1.0)

# Print report
backtester.print_backtest_report(results)
```

Output:
```
================================================================================
BACKTEST RESULTS
================================================================================

📊 SpatialArbitrage
────────────────────────────────────────────────────────────────────────────
Period: 2025-11-08 to 2025-11-15
Total Signals: 23
Trades Taken: 23

🎯 Performance:
  Win Rate: 69.6% (16W / 7L)
  Total Return: +31.50¢
  Avg Return/Trade: +1.37¢

📈 Risk Metrics:
  Sharpe Ratio: 2.14
  Max Drawdown: -4.20¢

💰 Edge:
  Average Edge: 2.35¢
  Best Trade: +8.50¢
  Worst Trade: -2.10¢
```

---

## ⚙️ Configuration

### Adjust Collection Frequency

Edit `run_data_collection.py`:

```python
# At the top of the file:
COLLECTION_INTERVAL = 300  # Change to 180 for 3 minutes
SIGNAL_INTERVAL = 600      # Change to 300 for 5 minutes
```

### Adjust Signal Filters

```python
MIN_EDGE_TO_LOG = 1.0        # Only log signals with >1¢ edge
MIN_CONVICTION = "MEDIUM"    # Only log MEDIUM+ conviction
SIGNAL_EXPIRY_HOURS = 24     # Auto-close signals after 24h
```

---

## 📂 Data Storage

All data is stored in SQLite database:
```
data/oracle_data.db
```

### Tables Created

1. **market_snapshots**: Raw order book data
2. **signals**: All signals logged by Oracle
3. **signal_updates**: Price updates for active signals
4. **collection_runs**: Metadata about collection cycles

### Export Data

```python
from modules import DataCollector

collector = DataCollector()
collector.export_data("data/my_export.csv")
```

---

## 🛠️ Troubleshooting

### No Data Being Collected

**Problem**: `total_snapshots: 0`

**Solutions**:
1. Check if markets are configured: `config/markets.py`
2. Verify connectors are running: Check logs
3. Ensure simulation mode is on (or API keys configured)

### No Signals Generated

**Problem**: `total_signals: 0`

**Solutions**:
1. Lower `MIN_EDGE_TO_LOG` to 0.5
2. Change `MIN_CONVICTION` to "LOW"
3. Wait longer (signals come every 10 minutes, not every cycle)

### Database Locked Errors

**Problem**: `database is locked`

**Solution**:
```bash
# Stop all running scripts
# Then restart with only one instance
```

---

## 📊 Expected Performance Timeline

### Day 1-2
- **Data**: 500-1000 snapshots
- **Signals**: 10-20 logged
- **Status**: Building dataset

### Day 3-5
- **Data**: 1500-2500 snapshots
- **Signals**: 30-50 logged
- **Status**: Patterns emerging

### Day 7
- **Data**: 2000-3000 snapshots
- **Signals**: 50-100 logged
- **Status**: **READY TO BACKTEST**

### Week 2+
- **Data**: 5000+ snapshots
- **Signals**: 150+ logged
- **Status**: **VALIDATED - READY TO TRADE**

---

## 🎯 What To Do With The Data

### Week 1: Observe

- Watch signals being generated
- See which strategies fire most often
- Note conviction levels
- Track which markets are most active

### Week 2: Analyze

- Run backtests
- Calculate win rates
- Identify best strategies
- Find optimal parameters

### Week 3: Optimize

- Tune parameters based on results
- Adjust edge thresholds
- Focus on best-performing markets
- Prepare for live trading

### Week 4: Deploy

- **If win rate > 65%** and **avg edge > 2.5¢**:
  - ✅ Ready to trade with real money
  - Start with $100-500
  - Only take HIGH conviction signals
  - Track every trade

---

## 🔐 Security Notes

- Database is **gitignored** (won't be committed)
- Logs are **gitignored** (won't be committed)
- No API keys stored in database
- All data is **local only**

---

## 💡 Pro Tips

### 1. Run Overnight

Data collection works best when running 24/7:
```bash
# Use tmux or screen to keep it running after logout
tmux new -s oracle
python run_data_collection.py

# Detach: Ctrl+B, then D
# Reattach later: tmux attach -t oracle
```

### 2. Monitor Logs

```bash
# Watch live logs
tail -f logs/data_collection.log

# Search for errors
grep ERROR logs/data_collection.log
```

### 3. Backup Data

```bash
# Backup database weekly
cp data/oracle_data.db data/backups/oracle_data_$(date +%Y%m%d).db
```

### 4. Check Disk Space

```bash
# Database grows ~10-20 MB per week
du -h data/oracle_data.db
```

---

## 🎓 Next Steps

1. ✅ **Launch data collection** (right now)
2. ✅ **Let it run for 7 days**
3. ✅ **Review signals daily** (learn patterns)
4. ✅ **Run backtests** (validate performance)
5. ✅ **Optimize parameters** (tune for your markets)
6. ✅ **Go live** (when validated)

---

## 📞 Quick Reference

### Start Collection
```bash
python run_data_collection.py
```

### Check Performance
```python
from modules import SignalTracker
SignalTracker().print_performance_report(days=7)
```

### Run Backtest
```python
from modules import Backtester
results = Backtester().backtest_all_strategies(days=7)
```

### Export Data
```python
from modules import DataCollector
DataCollector().export_data("my_export.csv")
```

---

**Remember**: The longer you collect data, the better your backtests. Give it at least 7 days before making decisions.

**The data doesn't lie. Let it run, let it learn, let it prove itself.**

🚀 **Launch it tonight. Have validated strategies by next week.**
