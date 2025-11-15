# 🎯 THE ORACLE STRATEGY GUIDE

**Master the 5 Alpha-Generating Strategies**

This guide explains each strategy in detail, when to use it, what to look for, and how to maximize your edge.

---

## 📚 Table of Contents

1. [BiasCorrector (Théo Strategy)](#1-biascorrector-théo-strategy)
2. [Favorite-Longshot Adjuster](#2-favorite-longshot-adjuster)
3. [Risk-Free Rate Adjuster (Domer Strategy)](#3-risk-free-rate-adjuster-domer-strategy)
4. [Dutch Book Detector](#4-dutch-book-detector)
5. [Spatial Arbitrage Detector](#5-spatial-arbitrage-detector)
6. [Combining Strategies](#6-combining-strategies-power-moves)
7. [Signal Quality Framework](#7-signal-quality-framework)

---

## 1. BiasCorrector (Théo Strategy)

### 🎓 **The Concept**

**The Problem**: Traditional polls lie. Not intentionally - but people hide controversial opinions from pollsters due to "social desirability bias."

**The Solution**: The "Neighbor Method" - instead of asking "Who will YOU vote for?", ask "Who will your NEIGHBORS vote for?"

**Why It Works**: People project their hidden preferences onto their neighbors, OR they accurately observe their local environment without the reputational cost of admitting their own view.

### 💰 **The $50M Trade**

Théo (the "Trump Whale") used this exact strategy in 2024:
- Public polls: Trump 48%, Harris 52% (dead heat)
- Neighbor polls: Trump 53%, Harris 47% (clear lead)
- **Théo's model**: Trump 51.5% true probability
- **Market price**: 48 cents
- **Edge**: +3.5 cents
- **Position size**: $50+ million
- **Outcome**: Trump won. Théo made $50M+.

### 📊 **What To Look For**

#### **The Shy Voter Index**
```
Shy_Index = Neighbor_Preference - Self_Preference
```

**Interpretation:**
- `Shy_Index > +3%`: Strong hidden support (BUY signal)
- `Shy_Index = 0%`: No bias (trust market price)
- `Shy_Index < -3%`: Reverse bias (rare, but possible)

#### **Example Calculation**

```
Self Poll: 48% say "I will vote for X"
Neighbor Poll: 53% say "My neighbors will vote for X"

Shy_Index = 53% - 48% = +5%

Model Fair Value = 48% + (5% × 0.75) = 51.75%
```

*Note: The 0.75 is the "shy_voter_weight" - how much you trust the neighbor signal.*

### ⚡ **When To Use**

**BEST:**
- Political elections (presidential, congressional)
- Controversial candidates or policies
- High-emotion topics (abortion, immigration, etc.)
- When public polls show tight races

**DON'T USE:**
- Non-political markets
- When no "neighbor" polling data exists
- Low-controversy candidates
- Markets with <$10k volume

### 🎯 **What Makes A GREAT Signal**

| Factor | Excellent | Good | Marginal |
|--------|-----------|------|----------|
| **Shy Index** | >5% | 3-5% | 1-3% |
| **Edge** | >5¢ | 3-5¢ | 1-3¢ |
| **Sample Size** | >1000 | 500-1000 | <500 |
| **Market Liquidity** | >$100k | $50-100k | <$50k |

### 💡 **Pro Tips**

1. **Weight Recent Polls More**: A 2-day-old neighbor poll > 2-week-old self poll
2. **Look for Consistent Patterns**: If 3+ polls show the same shy index, confidence ↑
3. **Monitor Poll Quality**: Harris, Pew, YouGov > random Twitter polls
4. **Cross-Reference**: If polls AND betting markets both show shy effect = 🚀

### ⚠️ **Common Mistakes**

❌ Using self polls only (missing the whole point)
❌ Ignoring sample size
❌ Not adjusting for poll age
❌ Applying to non-political markets

---

## 2. Favorite-Longshot Adjuster

### 🎓 **The Concept**

**The Problem**: Prediction markets systematically misprice extremes:
- **Favorites** (>80% probability): UNDERPRICED
- **Longshots** (<20% probability): OVERPRICED

**Why**:
- Favorites: People fear being wrong on "sure things"
- Longshots: People buy them like lottery tickets

**The Edge**: This is a KNOWN, PERSISTENT bias. It doesn't go away.

### 📊 **The Math**

#### **Favorites Are Underpriced**

```
Example: "Will the sun rise tomorrow?"
True Probability: 99.99%
Market Price: 96¢
Edge: +3.99¢

Why? People think "what if I'm wrong?" and demand a discount.
```

#### **Longshots Are Overpriced**

```
Example: "Will aliens land in 2026?"
True Probability: 0.01%
Market Price: 2¢
Edge: -1.99¢

Why? People buy it for fun ("imagine if it happens!")
```

### ⚡ **When This Module Activates**

The FLB Adjuster doesn't generate signals - it **enhances conviction** on signals from other modules.

#### **HIGH Conviction Boost**

1. **Buying an underpriced favorite**
   - Your model: Fair Value = 85%
   - Market: 80¢
   - Signal: BUY
   - FLB says: "AMPLIFIED - you're buying a favorite that's underpriced"
   - **Conviction: HIGH** ⭐⭐⭐

2. **Selling an overpriced longshot**
   - Your model: Fair Value = 10%
   - Market: 15¢
   - Signal: SELL
   - FLB says: "AMPLIFIED - you're selling a longshot that's overpriced"
   - **Conviction: HIGH** ⭐⭐⭐

#### **LOW Conviction Warning**

3. **Buying a longshot** (fighting the bias)
   - Your model: Fair Value = 15%
   - Market: 12¢
   - Signal: BUY
   - FLB says: "⚠️ WARNING - you're buying a longshot (normally overpriced)"
   - **Conviction: LOW** ⚠️

4. **Selling a favorite** (fighting the bias)
   - Your model: Fair Value = 88%
   - Market: 92¢
   - Signal: SELL
   - FLB says: "⚠️ WARNING - you're selling a favorite (normally underpriced)"
   - **Conviction: LOW** ⚠️

### 🎯 **How To Use This**

**Rule #1**: Only take HIGH conviction signals
- If FLB says HIGH → bet big
- If FLB says LOW → skip OR bet tiny

**Rule #2**: When multiple strategies agree with FLB = MAX BET
- BiasCorrector says BUY at 51¢ fair value
- Market at 48¢ (favorite territory)
- FLB says HIGH conviction
- **This is your 10x trade** 🚀

### 💡 **Pro Tips**

1. **Trust the Warnings**: When FLB says LOW, the market is usually right
2. **Double Down on HIGH**: These are your bread-and-butter trades
3. **Use for Position Sizing**: HIGH = 10% of capital, LOW = 1% of capital

---

## 3. Risk-Free Rate Adjuster (Domer Strategy)

### 🎓 **The Concept**

**The Problem**: Long-duration "sure things" lock up your capital for months/years. That has a cost.

**The Solution**: Treat prediction markets like bonds. Compare their yield to risk-free alternatives (T-bills, USDC lending).

**Why It Works**: Most retail traders don't do this math. They see "98% chance" and buy at 96¢ without thinking about time.

### 💰 **The Math**

#### **Bad "Sure Thing"**

```
Market: "Will X happen by Dec 2026?"
Market Price: 98¢
Resolution: 12 months away
Probability: ~99% (very likely)

Your calculation:
Profit if win: $1.00 - $0.98 = $0.02
Return: 2.04%
Annualized: 2.04%

Risk-Free Rate (T-bills): 5.0%
Opportunity Cost: 5.0% - 2.04% = 2.96%

Verdict: SELL (or skip)
You're losing 2.96% per year by holding this instead of T-bills.
```

#### **Good "Sure Thing"**

```
Market: "Will Y happen by June 2026?"
Market Price: 90¢
Resolution: 6 months away
Probability: ~95%

Your calculation:
Profit if win: $1.00 - $0.90 = $0.10
Return: 11.1%
Annualized: 22.2% (6 months → annual)

Risk-Free Rate: 5.0%
Excess Return: 22.2% - 5.0% = +17.2%

Verdict: BUY
You're earning 17% MORE than risk-free alternatives.
```

### ⚡ **When To Use**

**BEST:**
- High-probability events (>80%)
- Long time to resolution (>6 months)
- Clear resolution criteria
- High liquidity

**DON'T USE:**
- 50/50 coin flips (probability risk >> time risk)
- Resolves in <3 months
- Ambiguous resolution terms

### 🎯 **The Domer Framework**

#### **Step 1: Calculate Implied Yield**

```
Implied Yield = (1 / Price)^(1/years) - 1
```

#### **Step 2: Compare to RFR**

```
If Implied Yield > RFR + 2% → BUY
If Implied Yield < RFR → SELL
Else → SKIP
```

#### **Step 3: Adjust for Risk**

- Certainty = 99%+: Require RFR + 1%
- Certainty = 90-99%: Require RFR + 3%
- Certainty = 80-90%: Require RFR + 5%

### 💡 **Pro Tips**

1. **Update RFR Weekly**: T-bill rates change. Your model should too.
2. **Factor in Withdrawal Time**: If capital is locked for a year, you need a premium.
3. **Look for "Fake Certainties"**: Market at 95¢ but event is only 80% likely? Sell it.

---

## 4. Dutch Book Detector

### 🎓 **The Concept**

**The Problem**: In markets with multiple outcomes (e.g., "Who will win the primary?"), the sum of all prices should = $1.00. When it doesn't, there's free money.

**Why It Happens**:
- Retail traders get excited about multiple candidates
- Each candidate's supporters bid up "their" person
- The sum exceeds $1.00

**The Edge**: Pure math. This is risk-free arbitrage.

### 💰 **The Math**

#### **Over-Round (Free Money)**

```
Market: "2028 Republican Primary"

Prices:
- Trump: 45¢
- DeSantis: 35¢
- Haley: 22¢
- Other: 3¢
─────────────
Total: 105¢ ← Should be 100¢!

The Trade:
1. SELL all four at current prices
2. Collect: $1.05
3. Pay out: $1.00 (only one can win)
4. Profit: $0.05 (5¢ risk-free)

Minus fees (1.5¢ total) = 3.5¢ net profit
```

#### **Under-Round (Also Free Money)**

```
Market: "Who will host the 2030 Olympics?"

Prices:
- Paris: 30¢
- LA: 25¢
- Tokyo: 20¢
- Other: 20¢
─────────────
Total: 95¢ ← Should be 100¢!

The Trade:
1. BUY all four at current prices
2. Pay: $0.95
3. Receive: $1.00 (one MUST win)
4. Profit: $0.05 (5¢ risk-free)

Minus fees (2¢ total) = 3¢ net profit
```

### ⚡ **When To Use**

**BEST:**
- Categorical markets (3+ mutually exclusive outcomes)
- High emotion / tribal markets
- Low liquidity markets
- New markets (before smart money arrives)

**DON'T USE:**
- Binary markets (only 2 outcomes)
- High liquidity (arb disappears quickly)

### 🎯 **Execution Strategy**

#### **Speed Matters**

Dutch Books close FAST. When you see one:

1. **Calculate net profit** (after all fees)
2. **If >0.5¢, execute immediately**
3. **Place all orders at once** (don't let market adjust)

#### **Fee Calculation**

```
Gross Profit = |Sum - 1.00|
Total Fees = (# of outcomes) × (fee per share)
Net Profit = Gross Profit - Total Fees

Minimum to execute: Net Profit > 0.5¢
```

### 💡 **Pro Tips**

1. **Monitor New Markets**: Fresh markets = more opportunities
2. **Set Price Alerts**: Get notified when sum deviates from $1.00
3. **Have Capital Ready**: Arbs disappear in minutes

### ⚠️ **Risks**

- **Resolution Ambiguity**: If "Other" wins, do you get paid?
- **Liquidity**: Can you actually fill all orders?
- **Fees**: Don't forget gas + exchange fees

---

## 5. Spatial Arbitrage Detector

### 🎓 **The Concept**

**The Problem**: The same event trades at different prices on Kalshi (regulated, US, fiat) and Polymarket (global, crypto).

**Why**:
- Different user bases (US vs global)
- Different currencies (USD vs USDC)
- Different onboarding friction
- Information travels at different speeds

**The Edge**: Buy where it's cheap, sell where it's expensive. Zero directional risk.

### 💰 **The Math**

#### **Classic Spatial Arb**

```
Market: "Will Trump win 2028?"

Kalshi:
- Best Bid: 50¢
- Best Ask: 51¢

Polymarket:
- Best Bid: 53¢
- Best Ask: 54¢

The Trade:
1. BUY on Kalshi at 51¢
2. SELL on Polymarket at 53¢
3. Gross Spread: 2¢
4. Fees: 1.5¢ (Kalshi 0.7% + Poly 2% + gas)
5. Net Profit: 0.5¢

Not huge, but it's RISK-FREE.
```

### ⚡ **When To Use**

**BEST:**
- High-volume events (elections, economics)
- News-driven markets (react faster)
- When one platform lags the other

**DON'T USE:**
- Illiquid markets (can't fill orders)
- Tiny spreads (<1.5¢ after fees)
- When you can't move capital quickly

### 🎯 **The 4 Spatial Arb Patterns**

#### **Pattern 1: Kalshi Lag**
- Breaking news hits
- Polymarket reacts instantly (global, 24/7)
- Kalshi lags (US business hours)
- **Trade**: Buy Kalshi, Sell Poly

#### **Pattern 2: Crypto Premium**
- Polymarket users bullish on everything
- Kalshi more conservative
- **Trade**: Buy Kalshi, Sell Poly

#### **Pattern 3: Regulatory Discount**
- Kalshi faces US regulations
- Polymarket more "wild west"
- **Trade**: Depends on which way it cuts

#### **Pattern 4: Capital Flow**
- One exchange has a sudden influx of capital
- Prices move before arbitrageurs correct
- **Trade**: Fade the move

### 💡 **Pro Tips**

1. **Capital Velocity Matters**: How fast can you move money between platforms?
2. **Monitor Both 24/7**: Set up alerts for price divergence
3. **Factor All Costs**: Exchange fees, gas, slippage, withdrawal time

### ⚠️ **Risks**

- **Platform Risk**: What if one exchange freezes withdrawals?
- **Regulatory Risk**: What if Kalshi bans your account?
- **Execution Risk**: Prices move while you're placing orders

---

## 6. Combining Strategies (Power Moves)

### 🚀 **The Ultimate Signal**

When multiple strategies align, you have a **10x opportunity**.

#### **Example: The Perfect Storm**

```
Market: "Will Trump win 2028?"

BiasCorrector:
✅ Neighbor polls: 53%
✅ Self polls: 48%
✅ Fair Value: 51.5%

FLB Adjuster:
✅ Market at 48¢ (under 50% = not quite favorite territory)
✅ But buying, so no warning
✅ Conviction: MEDIUM → HIGH (because buying near 50%)

Spatial Arb:
✅ Kalshi: 47¢ ask
✅ Polymarket: 49¢ bid
✅ Edge: +2¢

COMBINED SIGNAL:
Strategy: BUY Kalshi @ 47¢
Fair Value: 51.5¢
Total Edge: 4.5¢
Conviction: HIGH
Spatial Bonus: +2¢

This is a 10/10 signal. MAX POSITION SIZE.
```

### 🎯 **Signal Scoring System**

| Score | Signals Aligned | Example | Action |
|-------|----------------|---------|--------|
| **10/10** | 3+ strategies, all HIGH | Above example | Max bet (10% capital) |
| **8/10** | 2 strategies, HIGH + MEDIUM | BiasCorrector + FLB | Large bet (5-7%) |
| **6/10** | 1 strategy, HIGH conviction | Spatial arb only | Medium bet (3-5%) |
| **4/10** | 1 strategy, MEDIUM conviction | Single signal | Small bet (1-2%) |
| **2/10** | Any strategy, LOW conviction | Fighting FLB | Tiny/Skip |

---

## 7. Signal Quality Framework

### 📊 **The 5-Factor Quality Check**

Before taking ANY trade, check these 5 factors:

#### **1. Edge Magnitude**
- **Excellent**: >5¢
- **Good**: 3-5¢
- **Marginal**: 1-3¢
- **Skip**: <1¢

#### **2. Conviction Level**
- **Excellent**: HIGH (strategies align)
- **Good**: MEDIUM
- **Marginal**: LOW
- **Skip**: Strategies conflict

#### **3. Liquidity**
- **Excellent**: >$100k volume
- **Good**: $50-100k
- **Marginal**: $10-50k
- **Skip**: <$10k

#### **4. Time to Resolution**
- **Excellent**: <30 days (fast feedback)
- **Good**: 30-90 days
- **Marginal**: 90-180 days
- **Careful**: >180 days (factor in RFR)

#### **5. Resolution Clarity**
- **Excellent**: Objective data source (BLS, NOAA)
- **Good**: Clear criteria, trusted oracle
- **Marginal**: Committee vote
- **Skip**: Ambiguous terms

### ✅ **The Decision Matrix**

```
IF edge > 5¢ AND conviction = HIGH AND liquidity > $50k:
    → BET 10% of capital

ELIF edge > 3¢ AND conviction >= MEDIUM AND liquidity > $25k:
    → BET 5% of capital

ELIF edge > 2¢ AND conviction = MEDIUM:
    → BET 2% of capital

ELSE:
    → SKIP or bet <1% for learning
```

---

## 🎓 **Final Wisdom**

### **The 3 Rules of Oracle Trading**

1. **Quality Over Quantity**
   - One 10/10 signal > ten 6/10 signals
   - Wait for exceptional opportunities

2. **Let the Strategies Vote**
   - If strategies disagree, the signal is weak
   - When they all agree, bet big

3. **Track Everything**
   - Every signal, every outcome
   - Learn what works for YOU
   - Optimize based on results

### **The Path to $500k**

It's not about being right every time. It's about:
- **Finding the 10/10 signals** (they exist weekly)
- **Betting big when you have edge** (Kelly Criterion)
- **Compounding relentlessly** (reinvest profits)
- **Learning continuously** (track, analyze, improve)

**The Oracle finds the edge. You execute with discipline.**

---

*Now go find alpha. The strategies are proven. The system is ready. Your journey starts now.* 🚀
