# Installation Guide - Crude Oil Algorithmic Trading System

## Complete Step-by-Step Setup

This guide will walk you through the complete installation process for the Crude Oil Futures Algorithmic Trading System.

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Windows Installation](#windows-installation)
3. [Python Environment Setup](#python-environment-setup)
4. [NinjaTrader 8 Configuration](#ninjatrader-8-configuration)
5. [Testing the Installation](#testing-the-installation)
6. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Hardware

- **CPU:** Intel Core i5 or equivalent (4 cores)
- **RAM:** 8 GB (16 GB recommended)
- **Storage:** 10 GB free space (SSD recommended)
- **Network:** Stable internet connection (10+ Mbps)

### Software Requirements

- **Operating System:** Windows 10/11 (64-bit)
- **NinjaTrader 8:** Version 8.1.2 or later
- **Python:** Version 3.9, 3.10, or 3.11
- **Visual Studio:** 2019 or later (Community Edition acceptable)
- **.NET Framework:** 4.8 (included with Windows)

### Account Requirements

- **NinjaTrader Account:** Free simulation account (or funded account)
- **Data Feed:** Rithmic, Kinetick, or other NT8-compatible feed
- **Prop Firm Account:** (Optional) For live funded trading

---

## Windows Installation

### Step 1: Install NinjaTrader 8

1. **Download NinjaTrader 8:**
   - Visit: https://ninjatrader.com/
   - Click "Download" → "Free Download"
   - Run installer: `NinjaTrader-8.1.x.x-Setup.exe`

2. **Installation Settings:**
   - Choose installation directory (default: `C:\Program Files\NinjaTrader 8`)
   - Select "Complete Installation"
   - Install all components

3. **Initial Setup:**
   - Launch NinjaTrader 8
   - Create account or log in
   - Skip "Getting Started" wizard (we'll configure manually)

4. **Connect Data Feed:**
   - **Tools → Connections → Configure**
   - Add connection (Rithmic, Kinetick, Sim, etc.)
   - Test connection

### Step 2: Install Python

1. **Download Python:**
   - Visit: https://www.python.org/downloads/
   - Download Python 3.11.x (Windows installer 64-bit)

2. **Run Installer:**
   - ✅ **IMPORTANT:** Check "Add Python to PATH"
   - Click "Install Now"
   - Wait for completion
   - Click "Disable path length limit" if prompted

3. **Verify Installation:**
   ```cmd
   python --version
   # Should output: Python 3.11.x

   pip --version
   # Should output: pip 23.x.x
   ```

### Step 3: Install Visual Studio (Optional but Recommended)

For C# development and debugging:

1. **Download Visual Studio 2022 Community:**
   - Visit: https://visualstudio.microsoft.com/downloads/
   - Download "Community" edition (free)

2. **Installation:**
   - Select workloads:
     - ✅ **.NET desktop development**
     - ✅ **.NET Framework 4.8 development tools**
   - Install

---

## Python Environment Setup

### Step 1: Create Virtual Environment

```cmd
# Navigate to project directory
cd C:\AlgoTrading\CrudeOilAlgoSystem

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Your prompt should now show (venv)
```

### Step 2: Install Python Dependencies

```cmd
# Make sure virtual environment is activated
cd PythonML

# Install all required packages
pip install -r requirements.txt

# This will install:
# - pyzmq (ZeroMQ communication)
# - numpy (numerical computing)
# - pandas (data manipulation)
# - scikit-learn (machine learning)
# - tensorflow (deep learning)
# - matplotlib (plotting)
# - and others...
```

**Expected output:**
```
Collecting pyzmq>=25.1.0
  Downloading pyzmq-25.1.1-cp311-cp311-win_amd64.whl (1.0 MB)
Successfully installed numpy-1.24.3 pandas-2.0.2 pyzmq-25.1.1 ...
```

### Step 3: Verify Python Installation

```cmd
# Test imports
python -c "import zmq; import numpy; import pandas; import sklearn; print('All imports successful!')"

# Expected output:
# All imports successful!
```

---

## NinjaTrader 8 Configuration

### Step 1: Copy Strategy Files

**Option A: Manual Copy**

```cmd
# Copy main strategy
copy NinjaTraderStrategies\CrudeOilMasterStrategy.cs "%USERPROFILE%\Documents\NinjaTrader 8\bin\Custom\Strategies\"

# Copy ML client
copy NinjaTraderStrategies\MLSignalClient.cs "%USERPROFILE%\Documents\NinjaTrader 8\bin\Custom\Strategies\"
```

**Option B: Using File Explorer**

1. Navigate to project folder: `CrudeOilAlgoSystem\NinjaTraderStrategies\`
2. Copy files:
   - `CrudeOilMasterStrategy.cs`
   - `MLSignalClient.cs`
3. Navigate to: `C:\Users\YourName\Documents\NinjaTrader 8\bin\Custom\Strategies\`
4. Paste files

### Step 2: Install NuGet Packages in NinjaTrader

NinjaTrader 8.1.2+ includes NuGet support:

1. **Open NinjaTrader 8**

2. **Press F5** to open NinjaScript Editor

3. **Tools → Options → NuGet**

4. **Install Required Packages:**

   **A. NetMQ (ZeroMQ for .NET)**
   ```
   - Click "Browse"
   - Search: "NetMQ"
   - Select: NetMQ (version 4.0.1.13 or compatible with .NET Framework 4.8)
   - Click "Install"
   ```

   **B. Newtonsoft.Json**
   ```
   - Search: "Newtonsoft.Json"
   - Select: Newtonsoft.Json (version 13.0.3 or latest)
   - Click "Install"
   ```

5. **Verify Installation:**
   - **Tools → Options → NuGet → Installed**
   - Should see:
     - ✅ NetMQ
     - ✅ Newtonsoft.Json

### Step 3: Compile Strategies

1. **In NinjaScript Editor:**
   - Press **F5** or click **Compile**

2. **Check Output Window:**
   ```
   Compiling...
   Compile operation completed successfully with 0 errors
   ```

3. **If Errors Occur:**
   - Check that NuGet packages are installed
   - Verify .NET Framework 4.8 is installed
   - See [Troubleshooting](#troubleshooting) section

### Step 4: Configure File Paths

1. **Create Directory Structure:**
   ```cmd
   mkdir C:\AlgoTrading
   mkdir C:\AlgoTrading\Logs
   mkdir C:\AlgoTrading\Models
   mkdir C:\AlgoTrading\Data
   ```

2. **Copy Configuration Files:**
   ```cmd
   copy Config\NewsCalendar.csv C:\AlgoTrading\NewsCalendar.csv
   copy Config\strategy_config.json C:\AlgoTrading\strategy_config.json
   copy Config\prop_firm_profiles.json C:\AlgoTrading\prop_firm_profiles.json
   ```

3. **Update Paths in Strategy:**
   - Open NinjaTrader
   - **Tools → Edit NinjaScript → Strategy → CrudeOilMasterStrategy**
   - Find line: `NewsCalendarPath = @"C:\AlgoTrading\NewsCalendar.csv"`
   - Verify path is correct for your system

---

## Testing the Installation

### Test 1: Python ML Server

1. **Open Command Prompt:**
   ```cmd
   cd C:\AlgoTrading\CrudeOilAlgoSystem\PythonML

   # Activate virtual environment
   ..\venv\Scripts\activate

   # Start server
   python ml_signal_server.py --host 127.0.0.1 --port 5555
   ```

2. **Expected Output:**
   ```
   ╔════════════════════════════════════════════════════════════════╗
   ║                                                                ║
   ║          Crude Oil ML Signal Server - 2025                     ║
   ║                                                                ║
   ║  Listening on: tcp://127.0.0.1:5555                            ║
   ║  Model Path: ./models                                          ║
   ║                                                                ║
   ║  Press Ctrl+C to stop the server                              ║
   ║                                                                ║
   ╚════════════════════════════════════════════════════════════════╝
   ```

3. **Test Connection (in new command prompt):**
   ```python
   python -c "import zmq; ctx = zmq.Context(); sock = ctx.socket(zmq.REQ); sock.connect('tcp://127.0.0.1:5555'); print('Connection successful!')"
   ```

### Test 2: NinjaTrader Strategy (Simulation)

1. **Open NinjaTrader 8**

2. **Create New Chart:**
   - **New → Chart**
   - Instrument: `CL 12-25` (or current front month)
   - Type: Minute
   - Value: 1
   - Click OK

3. **Add Strategy to Chart:**
   - Right-click chart → **Strategies**
   - Select: **CrudeOilMasterStrategy**
   - Click **Add**

4. **Configure Strategy (use conservative settings for testing):**
   ```
   Strategy Selection:
   - Enable VWAP Mean Reversion: Yes
   - Enable EIA Momentum: No
   - Enable AMT: No

   Risk Management:
   - Daily Loss Limit: $500
   - Trailing Drawdown: $1000
   - Default Position Size: 1
   - Stop Loss Ticks: 30

   Prop Firm Compliance:
   - Enable Consistency Rule: No (for testing)
   - Enable News Filter: Yes
   - News Calendar Path: C:\AlgoTrading\NewsCalendar.csv

   ML Integration:
   - Enable Python ML: No (test later)

   VWAP Settings:
   - StdDev Multiplier: 2.0
   - Target Ticks: 20

   Regime Detection:
   - High Volatility Threshold: 45
   - Low Volatility Threshold: 30
   ```

5. **Apply and Enable:**
   - Click **Apply**
   - Click **OK**
   - Strategy should now be running on chart

6. **Check Output Window:**
   - **Tools → Output Window**
   - Look for:
   ```
   ========================================
   Crude Oil Master Strategy Initialized
   Starting Equity: $50,000.00
   Daily Loss Limit: $500.00
   Trailing Drawdown: $1000.00
   ========================================
   ```

### Test 3: End-to-End with ML

1. **Ensure ML Server is Running** (from Test 1)

2. **Reconfigure Strategy:**
   - Right-click chart → **Strategies → CrudeOilMasterStrategy → Configure**
   - **ML Integration:**
     - Enable Python ML: **Yes**
     - Server Address: 127.0.0.1
     - Server Port: 5555
   - Click **Apply** → **OK**

3. **Monitor Both Windows:**
   - **NinjaTrader Output Window:** Should show ML connection messages
   - **Python Server Terminal:** Should show incoming requests

4. **Expected NinjaTrader Output:**
   ```
   ML Client: Connected to tcp://127.0.0.1:5555
   ```

5. **Expected Python Server Output:**
   ```
   2025-11-17 10:30:00,000 - __main__ - INFO - Received request: {'request_type': 'signal', ...}
   2025-11-17 10:30:00,005 - __main__ - INFO - Sent response: {'status': 'success', 'signal': 1, ...}
   ```

---

## Troubleshooting

### Issue: Strategy Won't Compile

**Error:** `The type or namespace name 'NetMQ' could not be found`

**Solution:**
1. Verify NetMQ is installed:
   - NinjaTrader → Tools → Options → NuGet → Installed
2. If not listed, install manually:
   - Download NetMQ.dll compatible with .NET Framework 4.8
   - Copy to `C:\Users\YourName\Documents\NinjaTrader 8\bin\Custom\`
3. Restart NinjaTrader
4. Press F5 to recompile

### Issue: Python Import Errors

**Error:** `ModuleNotFoundError: No module named 'zmq'`

**Solution:**
```cmd
# Ensure virtual environment is activated
cd C:\AlgoTrading\CrudeOilAlgoSystem
venv\Scripts\activate

# Reinstall dependencies
cd PythonML
pip install --upgrade -r requirements.txt
```

### Issue: ML Server Won't Start

**Error:** `Address already in use`

**Solution:**
```cmd
# Check if port 5555 is in use
netstat -ano | findstr :5555

# If process found, kill it (replace PID)
taskkill /PID <PID> /F

# Or change port in both:
# - Python server: --port 5556
# - NinjaTrader strategy: PythonServerPort: 5556
```

### Issue: Strategy Can't Load News Calendar

**Error:** `ERROR LOADING NEWS CALENDAR: Could not find file 'C:\AlgoTrading\NewsCalendar.csv'`

**Solution:**
```cmd
# Verify file exists
dir C:\AlgoTrading\NewsCalendar.csv

# If not, copy from project
copy Config\NewsCalendar.csv C:\AlgoTrading\NewsCalendar.csv

# Verify in strategy parameters:
# News Calendar Path: C:\AlgoTrading\NewsCalendar.csv
```

### Issue: "Unmanaged" Strategies Not Working

**Error:** Orders aren't submitted or fills aren't detected

**Solution:**
1. Check that `IsUnmanaged = true` in strategy code
2. Verify OnExecutionUpdate is implemented
3. For Rithmic connections:
   - Use OnExecutionUpdate for immediate fill detection
   - Don't rely solely on OnOrderUpdate
4. Add debugging:
   ```csharp
   Print("Order submitted: " + entryOrder.Name);
   Print("Execution received: " + execution.Order.Name);
   ```

### Issue: Performance is Slow

**Symptoms:** Strategy lags, ML requests timeout

**Solutions:**

1. **Reduce ML Request Frequency:**
   - Only send data every 5-10 bars instead of every tick
   - Implement caching for repeated requests

2. **Optimize Python Server:**
   ```python
   # Use compiled models (not retraining on every request)
   # Ensure models are loaded once at startup
   ```

3. **Hardware:**
   - Close unnecessary programs
   - Use SSD for data storage
   - Increase RAM allocation if possible

### Issue: Backtests Don't Match Live Results

**Causes:**
- Tick Replay not enabled
- Slippage not configured
- Different data feeds (Kinetick vs Rithmic)

**Solution:**
1. **Always enable Tick Replay:**
   - Strategy Analyzer → Settings → Tick Replay: **ON**
2. **Configure realistic slippage:**
   - Commission: $4.12 per RT
   - Slippage: 2 ticks
3. **Use same data feed:**
   - Backtest with same provider as live (Rithmic preferred)

---

## Post-Installation Checklist

Before going live, verify:

- [ ] NinjaTrader 8 installed and updated to latest version
- [ ] Python environment working (all imports successful)
- [ ] Strategy compiles without errors in NinjaTrader
- [ ] ML server starts and responds to health checks
- [ ] News calendar file loads correctly
- [ ] Simulation testing runs for 1+ week without crashes
- [ ] All circuit breakers tested (DLL, trailing DD, consistency)
- [ ] Prop firm parameters configured correctly
- [ ] Monitoring and alerts set up
- [ ] Backup strategy exists (in case of failures)

---

## Next Steps

1. **Read Full Documentation:**
   - See `README.md` for complete feature guide

2. **Generate Test Data:**
   ```cmd
   cd Utils
   python data_fetcher.py --source sample --bars 1000 --output ../data
   ```

3. **Train ML Models:**
   ```cmd
   cd PythonML
   python train_models.py --data ../data/crude_oil_historical.csv --output ./models
   ```

4. **Run Backtests:**
   - Use NinjaTrader Strategy Analyzer
   - Test on 6-12 months of historical data
   - Verify performance metrics

5. **Paper Trade:**
   - Run in simulation for 2+ weeks
   - Monitor for any violations or bugs

6. **Go Live:**
   - Only after thorough testing
   - Start with 1 contract
   - Monitor closely for first week

---

## Support

If you encounter issues not covered here:

1. **Check GitHub Issues:**
   - https://github.com/yourusername/CrudeOilAlgoSystem/issues

2. **Documentation:**
   - https://github.com/yourusername/CrudeOilAlgoSystem/wiki

3. **Community:**
   - Discord: https://discord.gg/crudeoilalgo

---

**Installation complete! You're ready to start algorithmic trading with confidence.**

Good luck! 🚀
