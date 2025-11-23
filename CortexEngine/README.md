# THE CORTEX PROTOCOL

## Event-Driven Online Learning Trading Engine

**Target:** $10,000/month from Crude Oil Futures
**Architecture:** Hybrid (NinjaTrader 8 C# + Python River ML)
**Memory:** O(1) - Learns immediately, no batch storage

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     THE CORTEX PROTOCOL                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐           ┌──────────────────┐        │
│  │   THE BODY (C#)  │◄─────────►│  THE BRAIN (Py)  │        │
│  │   NinjaTrader 8  │  ZeroMQ   │   River ML       │        │
│  │                  │           │                  │        │
│  │  • Execute Trades│           │  • Gatekeeper    │        │
│  │  • Manage Risk   │           │  • ARF Model     │        │
│  │  • VWAP Logic    │           │  • Amplifier     │        │
│  │  • Send Features │           │  • Drift Detect  │        │
│  └──────────────────┘           └──────────────────┘        │
│           │                              │                  │
│           │      THE REFLEX              │                  │
│           │  (Immediate Learning)        │                  │
│           └──────────────────────────────┘                  │
│                                                              │
│  On Trade Close → Send PnL → Learn Immediately → Adapt      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. THE GATEKEEPER (Regime Filter)
Filters out high-risk market conditions BEFORE consulting the model.

```python
Conditions Blocked:
- ATR > 2.5 (High volatility - whipsaw risk)
- ATR < 0.5 (Low volatility - no movement)
- |Momentum| > 2% (Strong trend - avoid mean reversion)
- Outside 9am-3pm (Low liquidity)
```

### 2. THE BRAIN (Adaptive Random Forest)
Online learning model that updates IMMEDIATELY after each trade.

```python
Model: ARFClassifier (10 trees, adaptive to drift)
Training: O(1) per sample - no batch storage
Output: Probability of winning trade (0.0 - 1.0)
```

### 3. THE AMPLIFIER (Dynamic Position Sizing)
Scales position size based on model confidence.

```python
Confidence > 80%  →  3 contracts (MAX AGGRESSION)
Confidence > 65%  →  2 contracts (MODERATE)
Confidence > 50%  →  1 contract  (BASELINE)
Confidence < 50%  →  0 contracts (BLOCK)
```

### 4. THE REFLEX (Immediate Learning)
The moment a trade closes:
1. NinjaTrader calculates PnL
2. Sends TRAIN message to Python
3. Model updates immediately (O(1))
4. ADWIN checks for regime drift
5. Ready for next prediction

**This is what makes it "online learning"** - no batching, no retraining, immediate adaptation.

---

## Installation

### Prerequisites
- Python 3.9+
- NinjaTrader 8
- NetMQ NuGet package

### Step 1: Python Environment
```bash
cd CortexEngine/Python
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: NinjaTrader Setup
1. Copy `CortexMasterStrategy.cs` to:
   ```
   Documents\NinjaTrader 8\bin\Custom\Strategies\
   ```

2. Add NetMQ reference:
   - Right-click References → Add Reference
   - Browse to `Libs/NetMQ.dll`
   - Or use NuGet: `Install-Package NetMQ`

3. Compile the strategy (F5 in NT8 NinjaScript Editor)

### Step 3: Start the System
```bash
# ALWAYS start Python FIRST
# Terminal 1:
cd CortexEngine/Deploy
./start_cortex.sh  # or start_cortex.bat on Windows

# Then start NinjaTrader
# Add CortexMasterStrategy to a CL chart
```

---

## Message Protocol

### PREDICT Request (Bar Close)
```json
{
  "type": "PREDICT",
  "features": {
    "close": 72.45,
    "atr": 1.23,
    "rsi": 45.2,
    "volume": 15000,
    "hour": 10,
    "vwap_dist": -0.15,
    "momentum": 0.008
  }
}
```

### PREDICT Response
```json
{
  "signal": "GO",
  "contracts": 2,
  "confidence": 0.72,
  "regime": "OPTIMAL",
  "reason": "Conditions favorable"
}
```

### TRAIN Request (Trade Close)
```json
{
  "type": "TRAIN",
  "pnl": 150.00,
  "contracts": 2,
  "session_pnl": 450.00,
  "trades_today": 3
}
```

### TRAIN Response
```json
{
  "status": "LEARNED",
  "drift": "STABLE",
  "trade_count": 47,
  "accuracy": 0.6382,
  "recent_win_rate": 0.7000
}
```

---

## Risk Management

### Built-in Circuit Breakers
- **Daily Loss Limit:** Default $1,000 (configurable)
- **Max Trades Per Day:** Default 10 (configurable)
- **Stop Loss:** 25 ticks per trade
- **Profit Target:** 15 ticks per trade
- **Session Close:** Exits all positions 30s before close

### Position Sizing Rules
- Never more than 3 contracts
- Reduces to 0 in high-vol regimes
- Scales with confidence (not fixed)

---

## Why River (Not Sklearn)?

| Feature | Sklearn | River |
|---------|---------|-------|
| Memory | O(n) - stores all data | O(1) - constant |
| Training | Batch (refit entire model) | Incremental (update one sample) |
| Drift Detection | Manual | Built-in (ADWIN) |
| Speed | Slow for streaming | Designed for streaming |
| Use Case | Static datasets | **Live trading streams** |

**Critical:** Do NOT replace River with sklearn. The O(1) memory and incremental learning are essential for production trading.

---

## Expected Performance

### Warm-Up Period
- First 50 trades: Model is learning, expect ~50% accuracy
- Trades 50-100: Model improving, ~55-60% accuracy
- Trades 100+: Model stabilized, ~60-65% accuracy

### After Calibration
| Metric | Target |
|--------|--------|
| Win Rate | 60-65% |
| Profit Factor | 1.35-1.50 |
| Monthly PnL (1 contract) | $3,000-4,000 |
| Monthly PnL (dynamic 1-3) | $7,000-10,000 |
| Max Drawdown | <$5,000 |

### Drift Events
When ADWIN detects drift:
- Model accuracy drops temporarily
- System will adapt over 20-30 trades
- Consider reducing position size manually

---

## Troubleshooting

### "Connection Failed" in NinjaTrader
1. Is Python script running FIRST?
2. Check firewall allows port 5555
3. Check `tcp://localhost:5555` is correct

### "No Response in 5 Seconds"
1. Python script may have crashed
2. Check Python console for errors
3. Restart Python script

### Model Not Improving
1. Check trade count (needs 50+ to stabilize)
2. Look for drift events in logs
3. Verify PnL is being sent correctly

### High Loss Rate
1. Check if market is in HIGH_VOL regime
2. Consider tightening gatekeeper thresholds
3. Reduce position size manually

---

## File Structure

```
CortexEngine/
├── Python/
│   ├── cortex_server.py    # THE BRAIN (River ML + ZeroMQ)
│   ├── requirements.txt    # Dependencies
│   └── venv/               # Virtual environment
├── NinjaTrader/
│   ├── CortexMasterStrategy.cs  # THE BODY (Execution)
│   └── Libs/
│       └── NetMQ.dll       # ZeroMQ library
├── Deploy/
│   ├── start_cortex.bat    # Windows startup
│   └── start_cortex.sh     # Linux/Mac startup
└── README.md               # This file
```

---

## Compared to Original System

| Feature | Original (CrudeOilMasterStrategy) | Cortex Protocol |
|---------|----------------------------------|-----------------|
| ML Type | Batch (retrain periodically) | Online (learn every trade) |
| Memory | O(n) - stores history | O(1) - constant |
| Adaptation | Manual retraining | Automatic |
| Drift Detection | None | ADWIN |
| Position Sizing | Fixed 1-3 | Confidence-based 0-3 |
| Architecture | Monolithic C# | Hybrid C# + Python |

**Cortex is the evolution** - same VWAP strategy, smarter adaptation, dynamic sizing.

---

## License & Disclaimer

This is for educational purposes. Trading futures involves substantial risk of loss. Past performance does not guarantee future results. Do not trade with money you cannot afford to lose.

---

**Version:** 1.0
**Author:** Cortex Protocol Development Team
**Last Updated:** November 2025
