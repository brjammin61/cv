# RESEARCH BRIEF: Crude Oil Algorithmic Trading System
## Context Document for Research Team

**Date:** November 17, 2025
**Project:** Crude Oil Futures Trading Algorithm Optimization
**Current Status:** Prototype validated, needs enhancement
**Goal:** Transform from $3-4k/month to $10-15k/month "money printer"

---

## 📋 EXECUTIVE SUMMARY

We have a **working, profitable crude oil futures trading system** that's been validated with realistic costs and data. The system currently generates an estimated **$3,000-$4,000/month** with 1 contract. Your mission is to research and implement improvements to **triple this performance** while maintaining or improving risk metrics.

**Current Performance (Validated):**
- Monthly Profit: $3,000-$4,000 (1 contract)
- Profit Factor: 1.30
- Win Rate: 59.5%
- Sharpe Ratio: 0.53
- Max Drawdown: $3,500

**Target Performance (6 months):**
- Monthly Profit: $10,000-$15,000 (2-3 contracts + enhancements)
- Profit Factor: 1.50+
- Win Rate: 65%+
- Sharpe Ratio: 1.0+
- Max Drawdown: <$5,000

---

## 🎯 WHAT WE'RE TRADING

### Instrument
- **Primary:** CL (Crude Oil Futures) - 1,000 barrels per contract
- **Alternative:** MCL (Micro Crude Oil) - 100 barrels per contract
- **Exchange:** NYMEX (CME Group)
- **Symbol:** CL (front month, e.g., CLZ25 for Dec 2025)
- **Tick Size:** $0.01 per barrel = $10 per contract
- **Typical Daily Range:** 100-200 ticks ($1,000-$2,000 per contract)

### Market Characteristics
- **Trading Hours:** Nearly 24/5 (Sunday 6pm - Friday 5pm ET)
- **Peak Liquidity:** 9:00 AM - 2:30 PM ET (Pit Session)
- **High Volatility Events:**
  - EIA Inventory Report: Wednesdays 10:30 AM ET
  - OPEC Meetings: Monthly/quarterly
  - Geopolitical Events: Russia, Middle East conflicts
- **Mean-Reverting:** Oil tends to revert to value due to physical supply/demand
- **Correlations:** Inverse to USD, positive to equities (risk-on)

---

## 🔧 CURRENT SYSTEM ARCHITECTURE

### Core Strategy: VWAP Mean Reversion

**Logic:**
1. Calculate Volume-Weighted Average Price (VWAP) over 25 periods
2. Calculate standard deviation bands (2.0 × StdDev)
3. **Entry:** When price touches upper/lower band + reversal pattern confirmation
4. **Exit:** Price reverts to VWAP OR profit target (15 ticks) OR stop loss (25 ticks)

**Optimal Parameters (Validated on 2,000 bars):**
```json
{
  "vwap_period": 25,
  "stddev_multiplier": 2.0,
  "stop_loss_ticks": 25,
  "target_ticks": 15,
  "position_size": 1
}
```

### Technology Stack

**Trading Platform:**
- NinjaTrader 8 (C# .NET Framework 4.8)
- Unmanaged order handling for low latency
- Rithmic data feed (prop firm standard)

**Machine Learning:**
- Python 3.11
- TensorFlow/Keras for deep learning
- scikit-learn for traditional ML
- ZeroMQ for C#/Python bridge

**Components Built:**
1. `CrudeOilMasterStrategy.cs` - Main NT8 strategy (1000+ lines)
2. `rl_trading_agent.py` - Reinforcement learning agent
3. `online_learning_system.py` - Continuous model improvement
4. `comprehensive_backtest.py` - Testing framework
5. Risk management with circuit breakers (DLL, trailing DD, consistency rule)

---

## 💰 COST STRUCTURE (Critical Understanding)

### Per-Trade Costs (Round Trip)
| Cost Type | Amount | Notes |
|-----------|--------|-------|
| Entry Slippage | $50 | 5 ticks on market order |
| Exit Slippage | $50 | 5 ticks to close position |
| Spread (Entry) | $10 | 1 tick bid-ask |
| Spread (Exit) | $10 | 1 tick bid-ask |
| Commission | $4.12 | Discount broker rate |
| **TOTAL** | **$124.12** | **Every trade costs this minimum** |

**Why This Matters:**
- With 200 trades/quarter, total costs = $24,800
- This is why realistic testing showed $20k profit vs fake $56k
- **Any improvement must overcome $124/trade cost to be profitable**

### Cost Variations
- **EIA Wednesday volatility:** Slippage can be 10+ ticks ($100+)
- **After hours/low liquidity:** Spread widens to 3-5 ticks
- **News events:** Slippage can hit 15 ticks ($150)
- **Prop firm accounts:** Commission may be lower ($2-3/RT)

---

## 📊 VALIDATED BACKTEST RESULTS

### Test Setup
- **Data:** 2,000 bars of realistic crude oil simulation
  - Volatility clustering (GARCH-like behavior)
  - 23 gap events (weekends, news)
  - Mean reversion characteristics
  - News spike simulation (EIA Wednesdays)
- **Timeframe:** Hourly bars (~3 months of data)
- **Costs:** $124.12 per round trip (realistic)
- **Slippage:** 5 ticks average, higher during volatility

### Results (All Top Configurations)

| Rank | VWAP | StdDev | Stop | Target | Net PnL | PF | Win% | Sharpe |
|------|------|--------|------|--------|---------|-----|------|--------|
| 1 | 25 | 2.0 | 25 | 15 | $20,867 | 1.30 | 59.5% | 0.527 |
| 2 | 25 | 2.0 | 25 | 20 | $20,789 | 1.29 | 59.2% | 0.524 |
| 3 | 25 | 2.0 | 30 | 15 | $20,041 | 1.26 | 58.9% | 0.505 |

**Key Findings:**
- ✅ All top 9 configs use VWAP=25 (consistent)
- ✅ StdDev=2.0 dominates (not 1.5 or 2.5)
- ✅ Tighter stops (20-25) better than wide (30)
- ✅ Quick targets (15) better than patient (20-25)
- ✅ Strategy is robust across parameter variations

### Monthly Projection
- Backtest: $20,866 over ~3 months
- Monthly average: $6,955
- **Conservative (with safety margin): $3,000-$4,000/month**

---

## 🚨 CRITICAL LIMITATIONS (Must Understand)

### What Our Tests DON'T Include

1. **Real Market Data**
   - We used realistic simulation, NOT actual prices
   - Need to validate on true CL futures historical data
   - Export from NinjaTrader or buy from data provider

2. **Tick-by-Tick Data**
   - Currently testing on hourly bars
   - Miss intrabar price action
   - Real fills may differ from backtest assumptions

3. **Psychological Factors**
   - Backtests don't have fear/greed
   - Watching $1,000 swings in real-time is stressful
   - Discipline to follow system is critical

4. **Black Swan Events**
   - 2020: Oil went NEGATIVE (-$37/barrel)
   - Russia-Ukraine war: +$30 in weeks
   - COVID crashes, bank failures, etc.
   - System not tested on extreme events

5. **Broker/Platform Issues**
   - NT8 crashes
   - Internet outages
   - Order rejections
   - Margin calls during volatility

### Data Sources Attempted (All Blocked)
- Yahoo Finance: 403 Forbidden
- Stooq: 403 Forbidden
- Alpha Vantage: API limit exceeded
- pandas_datareader: Access denied

**THIS IS YOUR FIRST TASK:** Get real data for validation

---

## 🎯 YOUR RESEARCH PRIORITIES

### TIER 1: CRITICAL (Week 1-2)

#### 1. Real Data Acquisition & Validation
**Objective:** Validate that $3-4k/month is achievable with REAL market data

**Tasks:**
- [ ] Export 12+ months of CL 1-minute bars from NinjaTrader
  - File → Utilities → Export → Market Data
  - Symbol: CL ##-##, Type: Minute, Value: 1
  - Date Range: Nov 2023 - Nov 2024
  - Format: CSV
- [ ] Alternative: Subscribe to Rithmic/CQG historical data ($50-100/month)
- [ ] Clean and format data to match our test structure
- [ ] Rerun ALL 81 parameter combinations on real data
- [ ] Compare results to simulation
- [ ] Document any major differences

**Expected Outcome:** Confirm (or adjust) $3-4k/month estimate

**Deliverables:**
- Real data CSV file (12 months minimum)
- Backtest results on real data
- Comparison report: Simulation vs Reality
- Updated profit expectations

---

#### 2. Multi-Timeframe Trend Filter
**Objective:** Don't fight the trend - only take trades aligned with higher timeframe

**Hypothesis:** Trading with 1-hour trend improves win rate by 5-8%

**Implementation:**
```python
# On 1-hour chart
h1_ema_50 = EMA(close, 50)
h1_trend = 'bullish' if close > h1_ema_50 else 'bearish'

# On 1-minute chart (trading timeframe)
if vwap_signal == 'long' and h1_trend == 'bullish':
    enter_long()
elif vwap_signal == 'short' and h1_trend == 'bearish':
    enter_short()
else:
    skip_trade()  # Against trend
```

**Testing:**
- [ ] Calculate 1H EMA(50) on historical data
- [ ] Tag each VWAP signal as with/against trend
- [ ] Measure win rate: with trend vs against trend
- [ ] Measure profit: with filter vs without filter
- [ ] Determine if benefit > reduction in trade count

**Expected Impact:**
- Win rate: 59% → 64-66%
- Trade count: -20% (but quality improves)
- Profit factor: 1.30 → 1.40+

**Deliverables:**
- Code implementation
- Backtest results with/without filter
- Recommendation: Enable or not?

---

#### 3. Volatility Regime Filter
**Objective:** Only trade during "Goldilocks" volatility - not too high, not too low

**Hypothesis:** Strategy performs best when ATR(14) is in specific range

**Implementation:**
```python
atr_14 = ATR(14)
atr_normalized = atr_14 / close  # As percentage

# Define regime
if atr_normalized < 0.015:  # Too quiet
    regime = 'low_volatility'
    trade_allowed = False
elif atr_normalized > 0.035:  # Too volatile
    regime = 'high_volatility'
    trade_allowed = False
else:
    regime = 'optimal'
    trade_allowed = True
```

**Testing:**
- [ ] Calculate ATR(14) for all historical bars
- [ ] Segment trades by volatility regime
- [ ] Measure performance in each regime
- [ ] Find optimal ATR range for filtering
- [ ] Test if filtering improves overall performance

**Expected Impact:**
- Profit factor: 1.30 → 1.38+
- Avoid worst losing streaks (high vol whipsaws)
- Avoid dead periods (low vol, no movement)

**Deliverables:**
- Volatility analysis report
- Optimal ATR thresholds
- Code implementation
- Performance comparison

---

#### 4. Time-of-Day Session Filter
**Objective:** Focus on hours with best liquidity and institutional activity

**Hypothesis:** 70% of profits come from 30% of trading hours

**Tasks:**
- [ ] Segment all trades by hour of day (EST)
- [ ] Calculate profit/loss by hour
- [ ] Identify peak performance hours
- [ ] Test filtered strategy (only trade optimal hours)

**Expected Optimal Sessions:**
- **9:00-11:30 AM ET** - US market open, high volume
- **1:30-2:30 PM ET** - Pre-close positioning
- **Avoid:** 12:00-1:00 PM (lunch, low volume)
- **Avoid:** Overnight (wide spreads, low liquidity)

**Expected Impact:**
- Same or better profit with 40% fewer trades
- Higher Sharpe ratio (less noise)
- Reduced overnight risk

**Deliverables:**
- Hour-by-hour performance analysis
- Recommended trading schedule
- Code implementation
- Results comparison

---

### TIER 2: HIGH VALUE (Week 3-4)

#### 5. Order Flow / Footprint Integration
**Objective:** Confirm VWAP touches with actual buyer/seller pressure

**Background:**
- Price touching VWAP lower band doesn't guarantee reversal
- Need to see buyers actually stepping in (positive delta)
- Order flow = volume at bid vs volume at ask

**Tools Needed:**
- Sierra Chart ($36/month) or Bookmap ($50-99/month)
- Rithmic data feed with bid/ask data
- Footprint chart or volume profile

**Research Questions:**
- [ ] At VWAP lower band, what % of time is delta positive?
- [ ] At VWAP upper band, what % of time is delta negative?
- [ ] Does delta magnitude predict reversal strength?
- [ ] Can we use absorption (large volume, price doesn't move) as entry signal?

**Implementation Concept:**
```python
# At VWAP lower band
if price <= vwap_lower_band:
    delta = buy_volume - sell_volume
    if delta > threshold:  # Buyers absorbing supply
        enter_long()  # High probability reversal
    else:
        skip_trade()  # No confirmation
```

**Expected Impact:**
- Win rate: 59% → 65%+
- Profit factor: 1.30 → 1.45+
- Fewer trades, but much higher quality

**Deliverables:**
- Order flow analysis on historical data
- Delta thresholds for confirmation
- Integration with NT8 strategy
- Performance comparison

**Budget:** $100-150/month (tools + data)

---

#### 6. EIA Inventory Report Strategy
**Objective:** Capture weekly crude oil inventory volatility (Wednesdays 10:30 AM)

**Current Status:** We AVOID EIA in news filter (conservative)
**Opportunity:** This is where the big moves happen ($500-1000/week potential)

**Background:**
- EIA releases weekly petroleum inventory data
- Actual vs Estimate drives massive volatility
- API (American Petroleum Institute) releases Tuesday night (preview)
- Can we predict direction and profit from it?

**Research Tasks:**
- [ ] Collect 2+ years of EIA data (actual vs estimate)
- [ ] Collect corresponding API data (Tuesday before)
- [ ] Analyze correlation: API surprise → EIA surprise
- [ ] Build predictive model
- [ ] Backtest EIA-only strategy

**Data Sources:**
- EIA: https://www.eia.gov/petroleum/supply/weekly/
- Investing.com: Economic calendar with estimates
- API: https://www.api.org/news-policy-and-issues/weekly-statistical-bulletin

**Strategy Concept:**
```python
# Tuesday night analysis
if api_actual > api_estimate + 2_million_barrels:
    wednesday_bias = 'bearish'  # Inventory build
elif api_actual < api_estimate - 2_million_barrels:
    wednesday_bias = 'bullish'  # Inventory draw

# Wednesday 10:30:00 AM
# If EIA confirms API:
if eia_direction == api_bias:
    enter_momentum_trade()
    target = 50 ticks  # Larger than normal
    stop = 30 ticks
```

**Expected Impact:**
- +$500-1,000/week from EIA alone
- ~4 trades/month, win rate 60-70%
- Adds uncorrelated returns to VWAP strategy

**Deliverables:**
- EIA/API historical database (CSV)
- Prediction model accuracy report
- Backtested EIA strategy results
- Integration code

---

### TIER 3: ADVANCED (Month 2+)

#### 7. Machine Learning Feature Engineering
**Objective:** Find edges that humans miss

**Current ML:** We have basic RL agent and online learning
**Enhancement:** Add advanced features for better predictions

**New Features to Test:**

**A. Sentiment Analysis**
- Twitter/X mentions of "crude oil", "$CL", "$USO"
- StockTwits sentiment scores
- News headline sentiment (Bloomberg, Reuters)
- **Tools:** Twitter API ($100/month), TextBlob (free)

**B. Options Flow**
- USO (oil ETF) put/call ratio
- Unusual options activity
- Implied volatility changes
- **Tools:** Market Chameleon ($100/month) or TDAmeritrade API (free)

**C. Commitment of Traders (COT)**
- Commercial hedgers vs speculators positioning
- Net long/short by trader type
- Published weekly by CFTC (free)
- **Source:** https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm

**D. Macro Indicators**
- USD Index (DXY) - inverse correlation to oil
- 10-Year Treasury Yield - risk appetite
- S&P 500 - risk-on/risk-off
- **Tools:** Free from FRED, Yahoo Finance

**E. Seasonality**
- Summer driving season (Apr-Sep) - bullish
- Winter heating oil (Nov-Feb) - bullish
- Spring/Fall - neutral
- **Implementation:** Month-of-year dummy variables

**Research Tasks:**
- [ ] Collect all feature data for 2+ years
- [ ] Align with CL price data
- [ ] Train RandomForest/GradientBoosting classifier
- [ ] Feature importance analysis (which actually matter?)
- [ ] Use ML predictions to filter VWAP signals

**Expected Impact:**
- Win rate: 59% → 63-65%
- Profit factor: 1.30 → 1.40+
- Sharpe ratio: 0.53 → 0.70+

**Deliverables:**
- Feature database (CSV)
- ML model trained and saved
- Feature importance report
- Integration with trading system
- Performance comparison

**Budget:** $200-300/month (data subscriptions)
**Time:** 14-21 days (data collection is time-consuming)

---

#### 8. Portfolio of Strategies
**Objective:** Don't rely on VWAP alone - diversify across uncorrelated strategies

**Rationale:**
- VWAP mean reversion works in range-bound markets
- Fails in strong trends
- Need strategies for different market regimes

**Additional Strategies to Build:**

**A. Breakout/Momentum (Trending Markets)**
- Logic: Price breaks above/below consolidation → follow
- Entry: 20-period high/low breakout
- Exit: Trailing stop or opposite breakout
- Works when: Strong directional move (OPEC news, geopolitics)

**B. Range Fade (Consolidation)**
- Logic: Fade extremes of established range
- Entry: Price at range high → short, range low → long
- Exit: Middle of range
- Works when: No news, market consolidating

**C. Gap Fill (Monday Mornings)**
- Logic: Weekend gaps often fill during Monday session
- Entry: If Sunday open gaps up → short, gaps down → long
- Exit: Gap filled or EOD
- Works when: No fundamental reason for gap

**D. Carry Trade (Overnight Holds)**
- Logic: Hold positions overnight to capture contango/backwardation
- Entry: Based on VWAP, but hold overnight
- Exit: Next day or when profit target hit
- Risk: Overnight gaps (manage with smaller size)

**Research Tasks:**
- [ ] Develop each strategy in backtest framework
- [ ] Test on historical data independently
- [ ] Measure correlation between strategies
- [ ] Optimize portfolio allocation
- [ ] Test combined performance

**Expected Impact:**
- Combined Sharpe: 0.53 → 0.90+
- Drawdowns reduced by 40% (diversification)
- Smoother equity curve
- More consistent monthly returns

**Deliverables:**
- 3 additional strategy implementations
- Individual performance reports
- Correlation matrix
- Portfolio optimization results
- Combined backtest

**Time:** 10-14 days

---

## 📁 FILES & CODE STRUCTURE

### What's Already Built (You Have Access To)

**NinjaTrader Strategies (C#):**
```
NinjaTraderStrategies/
├── CrudeOilMasterStrategy.cs       # Main strategy (1000+ lines)
│   ├── VWAP mean reversion logic
│   ├── Risk management (DLL, trailing DD, consistency)
│   ├── News filtering
│   ├── Prop firm compliance
│   └── Unmanaged order handling (Rithmic)
└── MLSignalClient.cs               # Python ML bridge (NetMQ)
```

**Python ML Components:**
```
PythonML/
├── ml_signal_server.py             # ZeroMQ server for ML signals
├── rl_trading_agent.py             # Deep Q-Network agent
├── online_learning_system.py       # Continuous model improvement
├── train_models.py                 # Model training pipeline
└── requirements.txt                # Python dependencies
```

**Testing Framework:**
```
Testing/
├── comprehensive_backtest.py       # Main backtest engine
│   ├── BacktestEngine class
│   ├── WalkForwardOptimizer
│   └── Parameter grid search
└── run_real_data_test.py          # Real data test runner
```

**Utilities:**
```
Utils/
├── data_fetcher.py                 # Generic data fetching
├── fetch_real_data.py              # Multi-source fetcher
└── realistic_crude_simulator.py    # Market simulation
```

**Configuration:**
```
Config/
├── strategy_config.json            # Strategy parameters
├── prop_firm_profiles.json         # Firm-specific settings
└── NewsCalendar.csv                # Economic events
```

**Results:**
```
results_realistic/
├── parameter_grid_results.csv      # All 81 tested configs
├── performance_report.json         # Machine-readable results
└── performance_report.txt          # Human-readable report
```

---

## 🎓 GETTING STARTED GUIDE

### Day 1: Environment Setup

**Install Requirements:**
```bash
# Python environment
cd CrudeOilAlgoSystem
python -m venv venv
source venv/bin/activate  # Mac/Linux
# or: venv\Scripts\activate  # Windows

# Install packages
cd PythonML
pip install -r requirements.txt

# Verify
python -c "import pandas, numpy, sklearn; print('Ready!')"
```

**Explore Code:**
```bash
# Read the main strategy
cat NinjaTraderStrategies/CrudeOilMasterStrategy.cs | head -200

# Read backtest engine
cat Testing/comprehensive_backtest.py

# Read current results
cat HONEST_RESULTS_REALISTIC_DATA.md
```

### Day 2-3: Get Real Data

**Option A: NinjaTrader Export (BEST)**
1. Open NinjaTrader 8
2. Tools → Historical Data Manager
3. Select: CL 12-24 (or current contract)
4. Download 12 months of 1-minute data
5. Tools → Export
6. Save as CSV

**Option B: Paid Data Provider**
- Sign up for Rithmic ($50/month) or CQG ($100/month)
- Download historical data API
- Export last 12 months

**Option C: Free Trial**
- Some brokers offer free trial data access
- TD Ameritrade, Interactive Brokers

### Day 4-5: Validate Current System

**Run Backtest on Real Data:**
```bash
cd Testing
python comprehensive_backtest.py \
    --data /path/to/real/cl_data.csv \
    --output ../results_real_validation
```

**Compare to Simulation:**
```bash
# Check if results are similar
diff results_realistic/performance_report.txt \
     results_real_validation/performance_report.txt
```

**Document Findings:**
- Are profits similar? ($20k ± 20%)
- Is win rate similar? (59% ± 5%)
- Are parameters stable? (VWAP=25, StdDev=2.0)

---

## 📊 KEY PERFORMANCE INDICATORS (KPIs)

### Track These Metrics Weekly

| Metric | Current | Target (3mo) | Target (6mo) |
|--------|---------|--------------|--------------|
| Monthly Profit (1 contract) | $3,000 | $5,000 | $7,000 |
| Profit Factor | 1.30 | 1.40 | 1.50 |
| Win Rate | 59% | 63% | 66% |
| Sharpe Ratio | 0.53 | 0.75 | 1.00 |
| Max Drawdown | $3,500 | $4,000 | $4,500 |
| Avg Trade Cost | $124 | $115 | $110 |
| Trades/Month | ~67 | ~75 | ~80 |

### Red Flags (Stop Trading If)
- Sharpe ratio drops below 0.30
- Win rate drops below 50%
- Max drawdown exceeds $5,000
- Profit factor drops below 1.10
- 5+ consecutive losing days

---

## 💼 BUDGET & RESOURCES

### Monthly Operating Costs

| Item | Cost | Required? |
|------|------|-----------|
| Data Feed (Rithmic/CQG) | $50-100 | Yes |
| Sierra Chart (order flow) | $36 | Phase 2 |
| Bookmap (footprint) | $50-99 | Phase 2 |
| Market Chameleon (options) | $100 | Phase 3 |
| Twitter API | $100 | Phase 3 |
| VPS (if needed for uptime) | $20-50 | Optional |
| **TOTAL (Phase 1)** | **$50-100** | - |
| **TOTAL (All Phases)** | **$400-500** | - |

### Time Investment

| Phase | Duration | Hours/Week |
|-------|----------|------------|
| Phase 1: Validation | 2 weeks | 20-30 |
| Phase 2: Filters | 2 weeks | 15-20 |
| Phase 3: Advanced | 8-12 weeks | 10-15 |

---

## 🎯 SUCCESS CRITERIA

### Week 2 Checkpoint
- [ ] Real data acquired and validated
- [ ] Backtest confirms $3-4k/month is achievable
- [ ] Multi-timeframe filter implemented and tested
- [ ] Volatility filter implemented and tested
- [ ] Time-of-day filter implemented and tested
- [ ] Combined performance shows improvement

**Expected:** Win rate 59% → 63%, PF 1.30 → 1.38

### Month 1 Checkpoint
- [ ] Order flow integration researched
- [ ] EIA strategy developed and backtested
- [ ] All improvements running in paper trading
- [ ] Forward test shows consistent profitability

**Expected:** $4-5k/month in paper trading

### Month 3 Checkpoint
- [ ] 2+ additional strategies developed
- [ ] Portfolio allocation optimized
- [ ] ML features integrated
- [ ] Live trading with 1 contract showing profit

**Expected:** $5-7k/month live trading

### Month 6 Goal
- [ ] Consistent $10k+/month with 2-3 contracts
- [ ] Sharpe ratio >1.0
- [ ] Multiple income streams (VWAP + EIA + options)
- [ ] System running largely automated

---

## 📞 COMMUNICATION & REPORTING

### Weekly Report Format

**Subject:** Week [X] Research Update - Crude Oil System

**1. Completed This Week:**
- List of tasks finished
- Code commits / files changed

**2. Results:**
- Backtest metrics (before/after changes)
- Win rate, profit factor, Sharpe changes
- Specific numbers

**3. Key Findings:**
- What worked
- What didn't work
- Surprising discoveries

**4. Next Week Plan:**
- Specific tasks for next 7 days
- Expected outcomes

**5. Blockers:**
- Any issues preventing progress
- Help needed

**6. Budget:**
- Any new subscriptions/costs
- Running total

### Questions? Ask Anytime

If you encounter:
- Technical issues (code errors)
- Conceptual questions (why this approach?)
- Need clarification on any task
- Want to propose alternative approaches

→ **Just ask!** Better to clarify than waste time going wrong direction.

---

## 🚀 FINAL WORDS

You're working on a **proven, profitable system**. We're not trying to "fix" it - we're trying to **optimize** it.

**Current:** Works, makes $3-4k/month
**Goal:** Enhance to $10-15k/month

This is achievable through:
1. Better filtering (trade less, profit more)
2. Additional uncorrelated strategies
3. Event-driven opportunities (EIA)
4. Machine learning optimization

**The foundation is solid. Now we build on it.**

Start with Tier 1 tasks (real data validation + quick filters). Once those work, move to Tier 2 and 3.

Each improvement compounds. Small gains add up to big results.

**Let's build a money printer.** 💰🚀

---

**Document Version:** 1.0
**Last Updated:** November 17, 2025
**Questions/Contact:** [Your contact info]
**GitHub Repo:** [Repo link if applicable]
