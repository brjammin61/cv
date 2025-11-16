# Multi-Token Mining Comparison

This document analyzes different mineable tokens on Solana to find the most profitable opportunities.

## Supported Mineable Tokens

### 1. ORE (oreoU2P8bN6jkk3jbaiVxYnG1dCXcYxwhwyK9jSybcp)
- **Type**: Proof-of-Work on Solana
- **Protocol**: ore.supply
- **Mining Client**: `ore-cli`
- **Typical Mining Cost**: 0.008-0.012 SOL per token
- **Market Price**: 0.010-0.015 SOL (varies)
- **Liquidity**: Good on Jupiter
- **Protocol Fee**: 10%

### 2. COAL (coaLSkmFF3pGFba8qCHhexfPaULBssTEeKxQjHFWPtn)
- **Type**: Proof-of-Work on Solana
- **Protocol**: coal.supply (sister of ore.supply)
- **Mining Client**: `coal-cli` (same as ore-cli, different flag)
- **Typical Mining Cost**: 0.005-0.010 SOL per token
- **Market Price**: 0.008-0.012 SOL (varies)
- **Liquidity**: Moderate on Jupiter
- **Protocol Fee**: 10%
- **Note**: Often CHEAPER to mine than ORE!

### 3. ORE v1 (Legacy)
- **Status**: Deprecated, but might still have liquidity
- **Not recommended** for new miners

## 📊 Profitability Comparison

Based on recent market data (simulated):

| Token | Avg Mining Cost | Avg Market Price | Profit Margin | Liquidity | Winner? |
|-------|----------------|------------------|---------------|-----------|---------|
| ORE   | 0.0095 SOL     | 0.0105 SOL      | ~9.5%        | High      | ⭐      |
| COAL  | 0.0060 SOL     | 0.0080 SOL      | ~25%         | Medium    | 🏆🏆🏆  |

**COAL might be 2-3x MORE profitable than ORE!**

## Why COAL Could Be Better:

1. **Lower Mining Difficulty**: Less competition = lower fees
2. **Higher Margins**: 25% vs 9.5% profit margin
3. **Same Infrastructure**: Uses same mining client as ORE
4. **Lower Market Price**: Easier to accumulate volume

## How to Mine COAL Instead:

### Quick Switch to COAL:

```bash
# Install coal-cli (same as ore-cli)
cargo install coal-cli

# Update your .env:
# Change these settings:
ORE_MINT=coaLSkmFF3pGFba8qCHhexfPaULBssTEeKxQjHFWPtn
MINER_PATH=coal
MINER_ARGS=mine --keypair wallet.json
```

### Or Mine BOTH (Multi-Token Strategy):

Run two bots in parallel:
- Bot 1: ORE arbitrage
- Bot 2: COAL arbitrage
- Both accumulate and compound!

## 🎯 Universal Multi-Token Bot (Coming)

We could build a bot that:
1. **Checks profitability** of ALL mineable tokens every cycle
2. **Auto-switches** to the most profitable token
3. **Mines the best opportunity** at any given moment
4. **Rebalances portfolio** automatically

**Example Decision Logic:**
```
Every 30 seconds:
  - Check ORE: mining cost vs market price
  - Check COAL: mining cost vs market price
  - Check OTHER: mining cost vs market price

  Decision: Mine whichever has highest profit margin!

  If ORE margin = 9%, COAL margin = 25%:
    → Switch to COAL mining!
```

## Other Potential Opportunities:

### GPU-Mineable Tokens:
Some Solana tokens might support GPU mining (faster than CPU):
- Higher hash rates = more rewards
- But higher electricity costs
- Need to calculate ROI

### Emerging Tokens:
Watch for NEW mineable tokens on Solana:
- Early mining = lower difficulty
- Potentially HUGE margins (100%+ early on)
- Higher risk (might not have liquidity)

## 🔬 Research Needed:

To find the BEST opportunity, we should:

1. **Live Market Data**: Check current prices for all tokens
2. **Mining Difficulty**: Test actual mining costs for each
3. **Liquidity Analysis**: Ensure we can actually sell what we mine
4. **Fee Comparison**: Some tokens might have lower protocol fees

## Want Me to Build It?

I can create:

1. **Multi-Token Profitability Scanner**
   - Scans ORE, COAL, and others
   - Shows real-time profit margins
   - Recommends best opportunity

2. **Auto-Switching Miner**
   - Mines most profitable token automatically
   - Switches between ORE/COAL/others
   - Maximizes total profit across all tokens

3. **Portfolio Optimizer**
   - Mines multiple tokens
   - Auto-sells at peaks
   - Rebalances for max returns

## Quick Test: COAL vs ORE

Let me check current market data for both:

```bash
# Test ORE profitability
./target/release/ore-simulator

# Test COAL profitability (need to build COAL version)
./target/release/coal-simulator
```

## ⚠️ Important Considerations:

**Liquidity Risk:**
- ORE has better liquidity (easier to sell)
- COAL has lower liquidity (might impact large sells)
- Need to consider slippage on swaps

**Market Volatility:**
- Smaller tokens = more price volatility
- Could work in our favor OR against us
- Need good risk management

**Network Effects:**
- ORE has more miners = higher difficulty
- COAL has fewer miners = lower difficulty (opportunity!)
- This changes over time

## Recommendation:

**Start with COAL testing!**

Why?
1. Potentially 2-3x higher margins
2. Same mining infrastructure as ORE
3. Lower competition
4. Easy to switch back to ORE if needed

**Test Strategy:**
1. Run COAL simulator to verify profitability
2. Mine COAL for 24 hours with small amount
3. Compare actual results vs ORE
4. Scale up whichever is more profitable

---

**Want me to:**
1. Build the COAL version of the bot?
2. Create multi-token profitability scanner?
3. Build auto-switching logic between ORE/COAL?
4. Research other mineable Solana tokens?

**The best mining opportunity might NOT be ORE!** 🚀
