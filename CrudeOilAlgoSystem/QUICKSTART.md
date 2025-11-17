# Quick Start Guide - Crude Oil Algorithmic Trading System

Get up and running in **15 minutes**!

## Prerequisites

- Windows 10/11 (for NinjaTrader)
- Python 3.9+ installed
- NinjaTrader 8 installed
- 30 minutes for testing

---

## 1. Setup Python Environment (5 minutes)

```bash
# Navigate to project directory
cd CrudeOilAlgoSystem

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
cd PythonML
pip install -r requirements.txt
```

**Verify:**
```bash
python -c "import zmq; print('ZeroMQ installed!')"
```

---

## 2. Generate Test Data (2 minutes)

```bash
cd ../Utils
python data_fetcher.py --source sample --bars 1000 --output ../data
```

**Output:** `data/crude_oil_historical.csv` (1000 bars of synthetic data)

---

## 3. Start ML Server (1 minute)

```bash
cd ../PythonML
python ml_signal_server.py
```

**Expected:**
```
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║          Crude Oil ML Signal Server - 2025                     ║
║                                                                ║
║  Listening on: tcp://127.0.0.1:5555                            ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
```

**Leave this running in the background.**

---

## 4. Install NinjaTrader Strategy (5 minutes)

### A. Copy Files

```batch
:: Copy strategy to NinjaTrader
copy NinjaTraderStrategies\CrudeOilMasterStrategy.cs "%USERPROFILE%\Documents\NinjaTrader 8\bin\Custom\Strategies\"

copy NinjaTraderStrategies\MLSignalClient.cs "%USERPROFILE%\Documents\NinjaTrader 8\bin\Custom\Strategies\"
```

### B. Install NuGet Packages

1. Open **NinjaTrader 8**
2. Press **F5** (NinjaScript Editor)
3. **Tools → NuGet Package Manager**
4. Install:
   - `NetMQ` (version 4.0.1.13)
   - `Newtonsoft.Json` (latest)
5. Press **F5** to compile

**Check for:** `Compile operation completed successfully with 0 errors`

### C. Copy Configuration

```batch
mkdir C:\AlgoTrading
copy Config\NewsCalendar.csv C:\AlgoTrading\NewsCalendar.csv
```

---

## 5. Run First Backtest (2 minutes)

1. **Open NinjaTrader**
2. **Tools → Strategy Analyzer**
3. **Settings:**
   - Instrument: `CL 03-25` (or current contract)
   - Type: `Minute`
   - Value: `1`
   - From: `30 days ago`
   - To: `Today`
4. **Strategy:** Select `CrudeOilMasterStrategy`
5. **Parameters (use defaults):**
   - Enable VWAP Mean Reversion: ✅
   - Daily Loss Limit: $1000
   - Stop Loss Ticks: 25
6. **Run**

**Expected:** Trades appear in results grid with profit/loss summary

---

## 6. Test Live in Simulation (Ongoing)

### A. Create Chart

1. **New → Chart**
2. Instrument: `CL 12-25` (current front month)
3. Type: `Minute`
4. Value: `1`

### B. Add Strategy

1. Right-click chart → **Strategies**
2. Select: `CrudeOilMasterStrategy`
3. **Configure (Conservative Settings):**

```
Strategy Selection:
✅ Enable VWAP Mean Reversion
❌ Enable EIA Momentum
❌ Enable AMT

Risk Management:
- Daily Loss Limit: $500
- Trailing Drawdown: $1000
- Position Size: 1
- Stop Loss Ticks: 30

Prop Firm Compliance:
❌ Enable Consistency Rule (for testing)
✅ Enable News Filter
- News Calendar Path: C:\AlgoTrading\NewsCalendar.csv

ML Integration:
❌ Enable Python ML (test without ML first)
```

4. **Apply** → **OK** → **Enable**

### C. Monitor

- **Tools → Output Window** - Watch for trade signals
- **Chart** - See strategy plotting
- **Account** - Monitor P&L

---

## 7. Understanding the Output

### NinjaTrader Output Window

```
========================================
Crude Oil Master Strategy Initialized
Starting Equity: $50,000.00
Daily Loss Limit: $500.00
========================================

VWAP LONG SIGNAL: Price 74.25 at Lower Band 74.20, Target VWAP 74.50
SUBMITTING LONG: Qty 1 @ Market, Stop 73.95, Target 74.50
EXECUTION: Entry Long filled 1 @ 74.26

PROFIT TARGET 1 SUBMITTED: Sell 1 @ 74.50
STOP LOSS SUBMITTED: Sell 1 @ 73.95

EXECUTION: Profit Target 1 filled 1 @ 74.51
Trade Closed: +$250
```

### Python ML Server Output

```
2025-11-17 10:30:15 - INFO - Received request: signal
2025-11-17 10:30:15 - INFO - Generated signal: 1 (Long) confidence: 0.82
2025-11-17 10:30:15 - INFO - Sent response
```

---

## Common First-Time Issues

### Issue: Strategy won't compile

**Fix:**
```
1. Verify NetMQ installed (Tools → NuGet → Installed)
2. Restart NinjaTrader
3. Press F5 to recompile
```

### Issue: ML server connection failed

**Fix:**
```
1. Check server is running (should see "Listening on..." message)
2. Verify port 5555 is free: netstat -an | findstr :5555
3. In strategy, set: Enable Python ML = No (for now)
```

### Issue: No trades being placed

**Reasons:**
- Market is closed (check session times)
- News blackout active (check calendar)
- VWAP bands not touched (price needs to deviate)
- Daily loss limit already hit

**Fix:**
```
1. Check Output Window for messages
2. Verify instrument has live data
3. Try on historical replay first (Strategy Analyzer)
```

---

## Next Steps

### Learn More

- **Full Documentation:** `README.md`
- **Detailed Installation:** `INSTALLATION.md`
- **Strategy Details:** See `README.md → Strategy Components`

### Optimize Performance

1. **Run Walk-Forward Optimization:**
   - Strategy Analyzer → Optimize → Walk-Forward
   - Test parameter stability

2. **Train Custom ML Models:**
   ```bash
   cd PythonML
   python train_models.py --data ../data/your_real_data.csv --output ../models
   ```

3. **Configure for Your Prop Firm:**
   - See `Config/prop_firm_profiles.json`
   - Adjust risk parameters accordingly

### Go Live (After Thorough Testing)

1. **Simulate for 2+ weeks** without violations
2. **Verify all circuit breakers work**
3. **Start with 1 contract**
4. **Monitor closely first week**
5. **Scale up gradually**

---

## Support

- **Issues:** https://github.com/yourusername/CrudeOilAlgoSystem/issues
- **Discussions:** https://github.com/yourusername/CrudeOilAlgoSystem/discussions
- **Discord:** https://discord.gg/crudeoilalgo

---

## Quick Reference Commands

```bash
# Activate Python environment
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

# Start ML server
cd PythonML && python ml_signal_server.py

# Generate sample data
python Utils/data_fetcher.py --source sample --bars 1000

# Train models
python PythonML/train_models.py --data data/crude.csv --output models/

# Fetch Yahoo Finance data
python Utils/data_fetcher.py --source yahoo --symbol CL=F --start 2020-01-01
```

---

**You're now ready to start algorithmic trading!** 🚀

Remember:
- ⚠️ **Always test in simulation first**
- ⚠️ **Never risk more than you can afford to lose**
- ⚠️ **Prop firm rules are strict - one violation = disqualification**

Happy trading!
