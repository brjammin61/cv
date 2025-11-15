# 📺 Watch The Oracle Live

**Real-time monitoring dashboard for the Oracle system**

## 🚀 Quick Start

```bash
streamlit run live_monitor.py
```

That's it! The dashboard will open in your browser.

---

## 🎯 What You'll See

### System Overview
- **Total Snapshots** - How much data collected
- **Total Signals** - Opportunities found
- **Active Signals** - Currently open positions
- **Closed Signals** - Completed trades

### Performance Metrics (Last 24h)
- **Signals Generated** - How many in the last day
- **Win Rate** - % of winning trades
- **Avg Edge** - Average edge per signal
- **Total P&L** - Paper trading profit/loss

### Recent Signals
- Last 20 signals generated
- Color-coded by conviction (GREEN=HIGH, YELLOW=MEDIUM, ORANGE=LOW)
- Shows strategy, market, edge, status, P&L
- Real-time updates

### Charts
- **Signals by Strategy** - Which strategies are firing
- **Signals by Conviction** - Quality distribution
- **Data Collection Stats** - Kalshi vs Polymarket

### Active Signals Detail
- All currently active positions
- Entry price vs current price
- Live P&L calculation
- Time opened

### System Logs
- Last 20 log entries
- Shows what the system is doing right now
- Errors and warnings highlighted

---

## ⚙️ Features

✅ **Auto-refreshes every 30 seconds**
- No need to manually refresh
- Always shows latest data
- Countdown timer shows next refresh

✅ **Clean, easy-to-read layout**
- Wide layout for maximum information
- Color-coded metrics
- Professional design

✅ **Live system status**
- Shows if Oracle is running
- Last data collection time
- System health

✅ **Real-time database queries**
- Reads directly from oracle_data.db
- No lag, no cache
- Instant updates

---

## 📊 Dashboard Sections

### 1. System Status Bar
```
✅ Oracle System: RUNNING
Auto-refresh in 27s
```

### 2. Quick Metrics (4 boxes)
```
Total Snapshots | Total Signals | Active Signals | Closed Signals
     2,451      |      47       |       3        |      12
```

### 3. Performance Dashboard
```
Signals Generated | Win Rate | Avg Edge | Total P&L
       12         |  66.7%   |  2.8¢    |  +18.5¢
```

### 4. Recent Signals Table
Scrollable table with last 20 signals:
- Timestamp
- Strategy (SpatialArb, BiasCorrector, etc.)
- Market name
- Signal type (BUY/SELL)
- Edge in cents
- Conviction (color-coded)
- Status (active/closed)
- P&L (if closed)

### 5. Strategy & Conviction Charts
Bar charts showing:
- Which strategies are generating signals
- Distribution of conviction levels

### 6. Data Collection Stats
- Snapshots per exchange
- Last collection time
- System uptime

### 7. Active Signals
Detailed view of open positions with live P&L

### 8. System Logs
Recent activity from the Oracle system

---

## 🎨 Color Coding

**Conviction Levels:**
- 🟢 **HIGH** - Green background
- 🟡 **MEDIUM** - Yellow background
- 🟠 **LOW** - Orange background

**P&L:**
- 🟢 **Profit** - Green background
- 🔴 **Loss** - Red background

**System Status:**
- ✅ **Running** - Green
- ❌ **Stopped** - Red

---

## 🔄 How It Works

1. **Dashboard starts** → Connects to `data/oracle_data.db`
2. **Queries database** → Gets latest stats, signals, snapshots
3. **Displays data** → Shows in clean, organized layout
4. **Waits 30 seconds** → Countdown timer
5. **Auto-refreshes** → Repeat from step 2

**All data is read-only** - Dashboard doesn't affect the Oracle system at all.

---

## 💡 Pro Tips

### Keep it open in a browser tab
- Leave it running while you work
- Glance over occasionally
- Watch signals appear in real-time

### Open multiple views
```bash
# Terminal 1: Watch live logs
tail -f logs/oracle_system.log

# Terminal 2: Dashboard
streamlit run live_monitor.py
```

### Check specific time periods
The dashboard shows:
- **Last 24 hours** for performance
- **Last 20** for recent signals
- **All time** for totals

### Watch for patterns
After a few days, you'll see:
- Which strategies fire most often
- What time of day signals appear
- Which markets are most active
- How ML optimization improves performance

---

## 🛠️ Troubleshooting

### Dashboard won't start
**Problem:** `streamlit: command not found`

**Solution:**
```bash
pip3 install streamlit
```

### No data showing
**Problem:** "Database not found"

**Solution:**
- Wait a few minutes for first data collection cycle
- Oracle system needs to run at least one cycle
- Check if Oracle is running: `ps aux | grep run_oracle_system`

### Dashboard is slow
**Problem:** Takes long to load

**Solution:**
- Normal on first load
- Subsequent refreshes are faster
- Database grows slowly, won't become an issue

---

## 📱 Access From Anywhere

### Local network access:
```bash
streamlit run live_monitor.py --server.address 0.0.0.0
```

Then open: `http://<your-ip>:8501`

### Default (local only):
```bash
streamlit run live_monitor.py
```

Opens: `http://localhost:8501`

---

## ⚡ Quick Commands

### Start dashboard:
```bash
streamlit run live_monitor.py
```

### Start in background:
```bash
nohup streamlit run live_monitor.py > /dev/null 2>&1 &
```

### Stop dashboard:
```bash
# Press Ctrl+C in the terminal
# Or kill the process:
pkill -f streamlit
```

### Restart dashboard:
```bash
pkill -f streamlit && streamlit run live_monitor.py
```

---

## 🎯 What To Watch For

### First 24 hours:
- **Data snapshots** should increase by ~288 (every 5 min = 12/hr = 288/day)
- **Signals** might be 0-10 (markets need to move for opportunities)
- **Win rate** will be N/A (no closed signals yet)

### After 2-3 days:
- **Signals** should be 20-50+
- **Win rate** starting to emerge
- **ML optimization** beginning to work
- **Patterns** becoming visible

### After 7 days:
- **Clear win rate** (goal: 65%+)
- **Consistent edge** (goal: 2.5¢+)
- **Strategy ranking** (which ones work best)
- **Ready to decide** on going live

---

## 📊 Example Dashboard View

```
🔮 The Oracle - Live System Monitor
Last updated: 2025-11-16 14:23:45

[Progress bar showing auto-refresh countdown]
Auto-refresh in 23s

✅ Oracle System: RUNNING

================================================================================
📊 System Overview
================================================================================

Total Snapshots     Total Signals     Active Signals     Closed Signals
    2,451               47                  3                 12

================================================================================
📈 Performance (Last 24 Hours)
================================================================================

Signals Generated    Win Rate    Avg Edge    Total P&L
       12            66.7%        2.8¢        +18.5¢

================================================================================
🎯 Recent Signals (Last 20)
================================================================================

[Table with 20 rows showing timestamp, strategy, market, signal, edge, conviction, status, P&L]

================================================================================
```

---

## 🚀 That's It!

Just run:
```bash
streamlit run live_monitor.py
```

And **watch the Oracle in action.**

**No configuration needed. Just works.**

---

**See you tomorrow at 9 AM for the first daily report!** 📊
