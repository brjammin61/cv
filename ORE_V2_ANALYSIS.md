# ORE V2 - Prospecting Game Arbitrage Bot

## How ORE V2 Actually Works

ORE V2 is NOT traditional proof-of-work mining. It's a prospecting game.

### Game Mechanics

**Each Round (1 minute):**
1. Miners deploy SOL on blocks in a 5x5 grid (25 blocks total)
2. At end of round, 1 winning block is chosen randomly (1/25 chance each)
3. **Winners** (miners on winning block):
   - Get back their deployed SOL
   - Receive portion of ALL losers' SOL (from other 24 blocks)
   - Share +1 ORE reward proportionally
   - OR one winner gets full +1 ORE (50% chance, weighted random)
4. **Losers** (miners on other 24 blocks):
   - Lose their deployed SOL (goes to winners)

**Motherlode Bonus:**
- Each round: +0.2 ORE added to motherlode pool
- 1/625 chance (0.16%) winning block hits motherlode
- If hit: pool split among winners
- If not hit: pool keeps growing

**Fees:**
- 10% refining fee on ORE rewards (redistributed to holders)
- 10% of SOL rewards used for ORE buyback
- 1% admin fee on deployed SOL
- Small transaction fees

## Expected Value Calculation

### Variables:
- `S` = SOL you deploy on your block
- `T` = Total SOL deployed across ALL 25 blocks
- `N` = Number of miners on your chosen block
- `M` = Your share on your block (S / total on your block)
- `P_win` = Probability your block wins = 1/25 (if random, but strategic placement changes this)

### If You Win:
```
Reward = Your deployed SOL back
       + (Total losing SOL × Your proportion on winning block)
       + (1 ORE × Your proportion) × 0.9  (after 10% refining fee)
       + Possible motherlode (0.16% chance)
```

### If You Lose (24/25 chance):
```
Loss = Your deployed SOL × 0.99  (after 1% admin fee)
```

### Expected Value:
```
EV = (1/25) × [S + (T - S_winning_block) × M + (1 ORE value) × M]
   - (24/25) × S

Simplified:
EV = (Winning rewards / 25) - (24S / 25)
```

### The Arbitrage Decision:

```python
acquisition_cost = (S - EV) / expected_ORE_received

if acquisition_cost < market_price_of_ORE:
    → PLAY THE ROUND
else:
    → BUY ORE ON DEX
```

## Strategic Considerations

### 1. Block Selection Strategy
**Question:** Which block to deploy on?

**Options:**
a) **Even distribution**: If all blocks equal, 1/25 win chance
b) **Underdog strategy**: Pick less popular blocks
   - Less competition on winning block = bigger share
   - But others might have same idea
c) **Whale following**: Pick blocks with most SOL
   - If you win, big rewards from losers
   - But smaller personal share
   - Risk: whales might know something

### 2. Capital Allocation
**Question:** How much SOL to deploy?

**Factors:**
- More SOL = bigger share IF you win
- More SOL = bigger loss if you lose (24/25 chance)
- Diminishing returns if block already has lots of SOL
- Kelly Criterion for optimal bet sizing

### 3. Timing
**Question:** Play every round or selective?

**Factors:**
- Network congestion affects transaction fees
- Other miners' behavior (more competition = lower EV)
- Market price volatility
- Motherlode accumulation (higher = better to play)

### 4. Risk Management
**Expected Loss:**
- You will LOSE 24 out of 25 rounds on average
- Need enough capital to weather losing streaks
- Variance is HIGH (gambling-like)

**Bankroll Management:**
- Never deploy more than X% of capital per round
- Account for losing streaks (can lose 50+ rounds in row)
- Consider volatility of ORE price

## Comparison to Market

### Cost to Acquire 1 ORE via Playing:

Assuming you play 25 rounds and win 1 on average:

```
Total SOL deployed: 25 × S
Expected SOL back: (24 × 0 losses) + (1 × winning rewards)
Net cost: Total deployed - SOL back
ORE received: ~1 ORE (from 1 win out of 25)

Acquisition cost per ORE = Net cost / 1 ORE
```

**Example:**
- Deploy 0.1 SOL per round
- Play 25 rounds
- Total: 2.5 SOL deployed
- Win 1 round: Get back 0.1 SOL + losers' SOL (say 2 SOL) + 1 ORE
- Net cost: 2.5 - 2.1 = 0.4 SOL for 1 ORE (after fees)
- **Acquisition cost: 0.4 SOL per ORE**

**Market Price:** 0.01 SOL per ORE

**Decision:** BUY ON MARKET! (40x cheaper!)

## The Arbitrage Opportunity

**When Playing is Profitable:**

1. **Low competition rounds**
   - Fewer miners = more losing SOL to winners
   - Higher EV per round

2. **High motherlode accumulation**
   - If pool is 100 ORE and you hit it = massive bonus
   - Changes expected value significantly

3. **Market price spike**
   - If ORE price surges to 0.5 SOL
   - Suddenly playing for 0.4 SOL cost is profitable

4. **Strategic edge**
   - If you can predict which blocks others won't pick
   - Higher personal share on winning block

**When Buying is Better:**
- Most of the time, honestly
- Market is liquid and cheap
- Playing has high variance and fees
- Unless you have inside info or edge

## Bot Strategy

### Core Decision Logic:

Every round (1 minute):
1. Calculate current game state:
   - Total SOL across all blocks
   - Distribution across blocks
   - Motherlode size
   - Number of active miners

2. Calculate expected value:
   - For each block, calculate EV of deploying X SOL
   - Factor in fees, win probability, expected rewards

3. Get market price:
   - Current ORE price on Jupiter

4. Make decision:
   ```
   IF best_block_EV > market_price:
       Deploy SOL on best block
   ELSE:
       Buy ORE on DEX
   ```

5. Risk management:
   - Track bankroll
   - Adjust bet size based on Kelly Criterion
   - Stop if losing streak too long

## Challenges

1. **High variance** - Can lose many rounds in row
2. **Game theory** - Other bots might be playing
3. **Information asymmetry** - Need to see what others are doing
4. **Timing** - Rounds are fast (1 minute)
5. **Transaction latency** - Need to submit before round ends
6. **Fees eat profits** - 1% admin + 10% refining + tx fees

## Conclusion

**ORE V2 is fundamentally different from mining.**

It's more like:
- A lottery with skill components
- Parimutuel betting
- Game theory competition
- Strategic capital allocation

**The arbitrage is:**
- Play when EV > market price
- Buy when market price < EV
- Manage risk carefully (high variance!)

**Reality check:**
- Market is probably efficient
- Hard to beat unless you have edge
- Buying might almost always be better
- Playing is more for fun/speculation

---

**Next: Build the V2-specific bot that:**
1. Monitors rounds in real-time
2. Analyzes block distributions
3. Calculates true EV per block
4. Compares to market price
5. Makes optimal play/buy decision
6. Manages bankroll and risk
