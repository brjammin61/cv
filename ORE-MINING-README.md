# ORE.supply Smart Mining Strategy v3.0

## 🎯 Executive Summary

**Fixed & Enhanced** ORE mining assistant for ore.supply. This improved version addresses critical bugs in the original strategy and adds performance tracking, better parsing, and more conservative risk management.

### Key Improvements Over v2.2:
1. ✅ **Fixed exploration bug** - tiles are now properly explored
2. ✅ **Improved parsing** - robust miners/stake extraction with validation
3. ✅ **Conservative sizing** - reduced overly aggressive bet scaling (1.30→1.15 gamma, 1.60→1.35 max scale)
4. ✅ **Performance tracking** - session stats, ROI, export functionality
5. ✅ **Better error handling** - graceful failures, validation, recovery
6. ✅ **Enhanced logging** - verbose mode for strategy debugging

---

## 🧠 Strategy Analysis

### Core Thesis (Sound ✓)
**Exploit crowd avoidance through:**
- Emptier tiles → higher b/W share → more rewards per SOL
- Fewer miners → less reward splitting
- Late timing → avoid last-second pile-ons
- Surge shield → skip stampede rounds

### Edge Components

#### 1. **Emptiness Learning (EWMA Bandit)**
- **Mechanism**: Tracks typical stake W per tile using exponential weighted moving average
- **Why it works**: Some tiles are habitually emptier due to miner psychology/patterns
- **Implementation**: `ewmaW = α*observed + (1-α)*ewmaW` with α=0.25
- **Exploration**: 10% epsilon-greedy to discover new patterns

#### 2. **Crowd Avoidance**
- **Signal**: Miner count per tile (when displayed)
- **Weight**: 45% crowd vs 55% emptiness in scoring
- **Rationale**: Even if stake is low, many miners = future dilution risk

#### 3. **Late Snipe**
- **Timing**: Acts at ≤5s remaining
- **Rationale**: Avoids early signaling; observes D buildup; reduces collision
- **Trade-off**: Risk of missing round vs. better tile selection

#### 4. **Surge Shield**
- **Detection**: If D increases ≥2 SOL in last 6 seconds, skip round
- **Rationale**: Late stampedes destroy EV via dilution
- **Calibration**: May need tuning based on typical round dynamics

#### 5. **Motherlode Boost**
- **Trigger**: When ML ≥ 50 ORE
- **Effect**: +1 tile (max 3) and 1.15x size multiplier
- **Rationale**: Higher jackpot = higher EV justifies more risk
- **Conservative**: Reduced from 1.20x to avoid over-betting

#### 6. **Adaptive k (Tile Count)**
- **Logic**: Fewer tiles when board is empty (concentrated bet), more when crowded (spread risk)
- **Thresholds**:
  - Median W < 0.40×avg → k=1 (very empty)
  - Median W < 0.75×avg → k=2 (moderately empty)
  - Otherwise → k=3 (crowded, spread risk)

#### 7. **Size Scaling**
- **Formula**: `amt = base × (avg_W / median_picked_W)^γ` where γ=1.15
- **Bounds**: 0.80x to 1.35x of base (was 0.75x to 1.60x)
- **Rationale**: If you find tiles 50% emptier, your share is already 2x better. Modest size increase captures more EV without excessive variance.
- **Criticism**: Could argue for NO scaling (Kelly criterion doesn't necessarily support this), but empirically it may work if edge is real.

---

## 🐛 Bugs Fixed in v3.0

### 1. **CRITICAL: Exploration Bonus Inverted**
**Original Bug:**
```javascript
// BUG: Exploration tiles scored 0-10, while typical W is 0.4-2.0
const emptinessScore = (Math.random()<0.10) ? (Math.random()*10) : prior;
// Result: Explored tiles got terrible scores (5-10) vs normal tiles (0.4-2.0)
// and were NEVER picked (opposite of intended exploration)
```

**Fix:**
```javascript
// Exploration tiles get random score in 0 to 50% of average (good score)
const emptinessScore = (Math.random()<0.10)
  ? (Math.random() * avg * 0.5)  // 0 to 0.3 if avg=0.6
  : prior;
```

**Impact**: High. Without exploration, strategy couldn't discover newly empty tiles or adapt to changing patterns.

---

### 2. **Fragile Miners/Stake Parsing**
**Original Issue:**
```javascript
// Heuristic: "last decimal = stake, integer before = miners"
// Problem: Fails if format changes, other numbers present, no decimal, etc.
```

**Fix:**
```javascript
// Strategy 1: Look for explicit "X SOL" and "Y miners" patterns
const solMatch = t.match(/(\d+\.\d+)\s*SOL/i);
const minersMatch = t.match(/(\d+)\s*miners?/i);

// Strategy 2: Fallback to heuristic with validation
// Strategy 3: Validate ranges (W: 0-1000, miners: 0-100k)
```

**Impact**: Medium. Improves reliability across UI changes and edge cases.

---

### 3. **Overly Aggressive Size Scaling**
**Original Parameters:**
```javascript
sizeScaleGamma: 1.30,   // Scale exponent
sizeScaleMax: 1.60      // Up to 1.6x base bet
// Example: If tiles 50% emptier → (1.0/0.5)^1.3 = 2.46x → capped at 1.6x
```

**Problem**: Betting 1.6x more when you already have 2x better share via lower W is double-dipping the edge. Increases variance without proportional EV gain.

**Fix:**
```javascript
sizeScaleGamma: 1.15,   // Reduced exponent
sizeScaleMax: 1.35,     // Cap at 1.35x
sizeScaleMin: 0.80      // Less aggressive reduction
// Same example: (2.0)^1.15 = 2.22x → capped at 1.35x (much more conservative)
```

**Impact**: High. Reduces risk of ruin while maintaining edge exploitation.

---

### 4. **No Performance Tracking**
**Original**: No way to know if strategy was profitable or validate EV claims.

**Fix**: Added comprehensive session tracking:
- Rounds played, total deployed, total claimed
- Per-round details (tiles, amounts, outcomes)
- Session ROI calculation
- Lifetime stats across sessions
- Export functionality for analysis

**Impact**: Critical for validation and tuning. Can now A/B test parameter changes.

---

### 5. **Missing Error Recovery**
**Original**: Parse failures, missing DOM elements caused silent failures or crashes.

**Fix**:
- Validation on all parsed values (range checks, type checks)
- Graceful degradation (if miners not parseable, ignore crowd signal)
- Status messages for common failures
- Retry logic with cooldowns

---

## 📊 Strategy EV Analysis

### When This Strategy Has Edge:

1. **Information asymmetry**: If miner counts/stakes aren't equally visible to all, you have an advantage
2. **Behavioral patterns**: If tiles have persistent emptiness patterns (location bias, superstition, UI quirks)
3. **Timing edge**: If late-sniping consistently finds better tiles than early entry
4. **Crowd psychology**: If surges are predictable and avoidable

### When This Strategy Might Fail:

1. **Efficient market**: If all miners use similar bots, crowd avoidance becomes a wash
2. **Site countermeasures**: If ore.supply randomizes rewards or adds anti-bot measures
3. **Small edge, high variance**: Even with positive EV, variance could cause drawdown
4. **Parameter miscalibration**: Wrong thresholds (surge detection, size scaling) could hurt EV

### Risk Factors:

| Risk | Severity | Mitigation |
|------|----------|------------|
| Variance/drawdown | High | Conservative sizing, round caps, stop loss |
| Bot detection | Medium | Wallet-safe mode, jitter, human-like timing |
| Market efficiency | High | Continuous monitoring, A/B testing, adaptation |
| Parse failures | Low | Validation, fallbacks, error handling |
| Overfitting | Medium | Exploration (10% epsilon), regularization |

---

## 🚀 Installation & Usage

### Prerequisites
- **Tampermonkey** browser extension ([Chrome](https://chrome.google.com/webstore/detail/tampermonkey/dhdgffkkebhmkfjojejmpbldmpobfkfo) | [Firefox](https://addons.mozilla.org/en-US/firefox/addon/tampermonkey/))
- Access to [ore.supply](https://ore.supply)

### Installation Steps

1. **Install Tampermonkey** in your browser (if not already installed)

2. **Open Tampermonkey Dashboard**:
   - Click the Tampermonkey icon in your browser toolbar
   - Select "Dashboard"

3. **Create New Script**:
   - Click the "+" icon or "Create a new script"
   - Delete the default template

4. **Paste the Script**:
   - Copy the entire contents of `ore-mining-strategy-improved.js`
   - Paste into the Tampermonkey editor
   - Save (Ctrl+S or Cmd+S)

5. **Navigate to ore.supply**:
   - Go to https://ore.supply
   - The script will auto-load
   - You should see a HUD panel in the bottom-left corner

### Configuration

#### Recommended Starting Settings (1 SOL bankroll):
```javascript
Base per-tile:    0.0008 SOL
k start:          2
Max rounds:       200
Round cap:        0.010 SOL
Gate D ≤:         20.0 SOL (only act if total deployed ≤ 20)
Snipe at ≤:       5 seconds

Toggles:
✓ adapt k
✓ low-crowd
✓ ML boost
✓ wallet-safe (DO NOT auto-deploy)
✗ highlight-only (would only show picks, not select)
✗ simulate
✗ verbose (enable for debugging)
```

#### Wallet-Safe Mode (RECOMMENDED):
**ON** (default): Script selects tiles and sets amount, but YOU manually click Deploy or let site's Auto handle it. NEVER accesses wallet.

**OFF** (risky): Script clicks Deploy button automatically. Still wallet-safe (no key access), but more automation = more risk.

#### For Testing/Learning:
- Enable **simulate** mode: No clicks, just highlights picks
- Enable **verbose** logging: See detailed decision reasoning in console
- Start with **highlight-only** to observe picks without any interaction

### Usage Workflow

1. **Configure** settings in HUD (or use defaults)
2. **Click "Start"** button
3. **Observe** status messages and tile selections
4. **In wallet-safe mode**: Script selects tiles; you click Deploy when ready
5. **Monitor** session stats (rounds, deployed, ROI)
6. **Click "Stop"** when done
7. **Export stats** for analysis (optional)

---

## 🎛️ Advanced Tuning

### Parameter Sensitivity Analysis

| Parameter | Impact | Tuning Guidance |
|-----------|--------|-----------------|
| `basePerTileSOL` | **High** | Scale with bankroll; ~0.05-0.15% of bankroll per tile |
| `kStart` | **Medium** | 2 is balanced; 1 if conservative, 3 if risk-tolerant |
| `gateTotalDeployed` | **High** | Lower = more selective (fewer rounds); tune to site activity |
| `snipeAtSec` | **Medium** | Lower = later entry = more info, but miss risk; 3-7s sweet spot |
| `sizeScaleGamma` | **High** | Lower = less aggressive; 1.0 = no scaling (Kelly-optimal?), 1.15 moderate |
| `surgeLookbackSec` | **Low** | Depends on round length; 4-8s reasonable |
| `surgeMinDeltaSOL` | **Medium** | Lower = more sensitive (skip more); tune to typical D variance |
| `mlSizeMultiplier` | **Low** | 1.1-1.2x conservative; 1.5x+ very aggressive |
| `minersWeight` | **Low-Med** | 0.4-0.5 if counts reliable; 0 to ignore crowd signal |

### A/B Testing Recommendations

Test one parameter at a time:

1. **Baseline**: Run 100 rounds with default settings, record ROI
2. **Variant**: Change ONE parameter (e.g., `sizeScaleGamma: 1.0`), run 100 rounds
3. **Compare**: Use exported stats JSON for statistical analysis
4. **Iterate**: Keep improvements, revert regressions

---

## 📈 Monitoring & Success Metrics

### Key Performance Indicators:

1. **ROI per session**: (claimed - deployed) / deployed
   - **Target**: >5% positive in 100+ round sample
   - **Acceptable**: -2% to +2% (could be variance)
   - **Concern**: <-5% (strategy may not have edge)

2. **Skip rate**: skipped_rounds / total_opportunities
   - **Healthy**: 10-30% (selective entry)
   - **Too high**: >50% (too conservative, missing +EV)
   - **Too low**: <5% (not filtering bad spots)

3. **Avg tiles picked per round**: Should align with board emptiness
   - **Very empty**: k=1 dominant
   - **Balanced**: k=2 dominant
   - **Crowded**: k=3 dominant

4. **Parsing success rate**: Check console for "n/a" or "Infinity" in verbose logs
   - **Target**: <5% parse failures
   - **Action if >20%**: DOM selectors need updating

### Red Flags:

- ⚠️ Consistent negative ROI over 200+ rounds → strategy has no edge or wrong params
- ⚠️ Frequent parse errors → site UI changed, needs selector updates
- ⚠️ Always picking same tiles → learning stuck, try resetting
- ⚠️ High variance, deep drawdowns → reduce bet size or increase k

---

## 🔧 Troubleshooting

### "Tiles not found" error
**Cause**: DOM selectors don't match current site structure
**Fix**: Inspect page, update `SEL.tileCandidates` in script

### Amount not setting correctly
**Cause**: Input selector wrong or input disabled
**Fix**: Check `SEL.amountInputs`, ensure not using site's Auto mode that locks input

### Tiles showing "W=Infinity" or "miners=n/a"
**Cause**: Parse failing due to unexpected format
**Fix**: Check console verbose logs, update `parseTileStakeAndMiners()` regex

### Strategy not picking any tiles (all skipped)
**Cause**: `gateTotalDeployed` too low or surge shield too sensitive
**Fix**: Increase gate or disable it (set to 0); adjust `surgeMinDeltaSOL`

### Wallet popup appearing unexpectedly
**Cause**: `walletSafeMode` is OFF and script is clicking Deploy
**Fix**: Enable wallet-safe mode or stop script before site initiates txs

---

## 🧪 Simulation Mode for Testing

Enable **simulate** mode to test without any real clicks:

```javascript
// In HUD, check:
✓ simulate
✓ verbose

// Script will:
// - Highlight picks (visual only)
// - Log decisions to console
// - NOT click tiles, set amounts, or deploy
// - Track "virtual" rounds in stats
```

Use this to:
- Validate tile selection logic
- Observe emptiness learning over time
- Test parameter changes risk-free
- Debug parsing issues

---

## 📝 Code Structure

```
Main Components:
├── CFG (Configuration)
├── Bandit (Learning/EWMA storage)
├── Stats (Performance tracking)
├── Parsers (DOM extraction)
│   ├── getTiles()
│   ├── parseTileIndex()
│   ├── parseTileStakeAndMiners()
│   └── readTotalDeployed/Timer/Motherlode()
├── Learning (EWMA updates)
├── Pick Logic (tile selection)
│   ├── pickTilesSmart() - main algorithm
│   ├── computePerTileSize() - sizing
│   └── Adaptive k
├── Safety (Surge shield, gates)
├── Auto-claim (optional)
├── HUD (UI panel)
└── Main Loop (orchestration)
```

---

## 🤔 Final Thoughts & Recommendations

### Is This Strategy Profitable?

**TL;DR**: **Maybe**. Depends on market efficiency and your edge vs. other miners.

**Bullish Case**:
- Information edge (learning tile patterns)
- Timing edge (late snipe avoids early dilution)
- Behavioral edge (crowd avoidance if others don't optimize)
- Risk management (surge shield, caps, gates)

**Bearish Case**:
- If everyone uses similar bots → edge disappears
- Variance could swamp small edge (need large sample)
- ORE mining economics may not support consistent arbitrage
- Solana tx fees + slippage could eat thin margins

### Best Practices:

1. **Start small**: 0.5-1 SOL bankroll, low base amounts
2. **Track everything**: Export stats every session, analyze in spreadsheet
3. **A/B test**: Change one param at a time, compare 100-round samples
4. **Stay updated**: If site changes UI/rules, update selectors/logic
5. **Know when to quit**: If negative ROI persists, strategy may not work
6. **Wallet safety**: ALWAYS keep wallet-safe mode ON unless you deeply trust the script

### Next-Level Improvements (For Developers):

1. **Machine learning**: Replace EWMA with more sophisticated models (LSTM, bandit algorithms)
2. **EV calculator**: Estimate per-round expected value based on D, W, k
3. **Dynamic parameters**: Auto-tune `snipeAtSec`, `gateD` based on recent rounds
4. **Ensemble strategy**: Run multiple strategies, pick best performer
5. **Statistical testing**: Implement proper hypothesis testing for parameter changes
6. **Backtesting framework**: Replay historical data to validate strategies
7. **Risk management**: Kelly criterion-based sizing, stop-loss, drawdown limits

---

## 📄 License & Disclaimer

**Disclaimer**: This script is for educational purposes. ORE mining involves risk. No guarantee of profit. Use at your own risk. Not financial advice.

**License**: MIT (modify and share freely)

---

## 🙏 Credits

- Original v2.2 strategy: Anonymous (provided for review)
- v3.0 improvements: Enhanced by Claude (Anthropic)
- ORE protocol: [ore.supply](https://ore.supply)

---

## 📊 Appendix: Example Stats Export

```json
{
  "bandit": {
    "arms": {
      "1": { "ewmaW": 0.523, "seen": 45, "lastSeenRound": 198 },
      "2": { "ewmaW": 0.789, "seen": 23, "lastSeenRound": 187 },
      ...
    },
    "rounds": 200
  },
  "stats": {
    "currentSession": null,
    "sessions": [
      {
        "startTime": 1700000000000,
        "endTime": 1700003600000,
        "durationMin": 60,
        "rounds": 200,
        "deployed": 0.16,
        "claimed": 0.172,
        "skipped": 35,
        "errors": 2,
        "roundDetails": [...]
      }
    ],
    "lifetime": {
      "rounds": 200,
      "deployed": 0.16,
      "claimed": 0.172,
      "netROI": 7.5
    }
  }
}
```

**Analysis**:
- ROI: +7.5% (good!)
- Skip rate: 35/235 = 14.9% (healthy selectivity)
- Avg deployed/round: 0.0008 SOL (matches base setting)
- Conclusion: Strategy showing positive edge in this sample

---

**END OF DOCUMENTATION**

For support or questions, open an issue in the repo or consult ORE mining community resources.

Good luck mining! ⛏️
