# Solana MEV Bot - Production Ready

A complete, production-ready MEV (Maximal Extractable Value) bot for Solana with 3 levels of strategies.

## 🚀 Quick Start

```bash
# 1. Copy and configure environment
cp ../.env.mev.example .env
nano .env  # Set your RPC_URL and WALLET_PRIVATE_KEY

# 2. Build the bot
cargo build --release

# 3. Test in dry-run mode (REQUIRED FIRST!)
DRY_RUN=true cargo run --release

# 4. After 24-48 hours of successful dry-run testing:
# Edit .env and set DRY_RUN=false
# Start with very small position sizes!
cargo run --release
```

## 📊 Features

### Level 1: Cross-DEX Arbitrage
- Monitors Jupiter, Raydium, Orca for price discrepancies
- Executes buy-low-sell-high across DEXs
- Fully accounts for ALL fees and slippage

### Level 2: Multi-Hop Arbitrage
- Finds circular arbitrage paths (SOL → USDC → BONK → SOL)
- Supports 2-4 hop paths
- Optimizes path selection for maximum profit

### Level 3: MEV Searcher
- Monitors mempool for large swaps
- Detects backrun opportunities
- Jito bundle integration for atomic execution
- Liquidation scanner (extensible)

### Risk Management
- Trade size limits
- Daily loss limits with auto-pause
- Circuit breakers on consecutive failures
- Real-time position tracking

### Profit Calculator
**THE CRITICAL COMPONENT** - Prevents "simulation-only" profits
- Accounts for transaction fees (base + priority)
- Protocol fees (DEX-specific)
- Slippage (both buy AND sell sides)
- Re-validates before execution

## 📁 Architecture

```
mev-bot/
├── src/
│   ├── main.rs                  # Entry point
│   ├── orchestrator.rs          # Main coordinator
│   ├── arbitrage_detector.rs   # Level 1 strategy
│   ├── multi_hop.rs             # Level 2 strategy
│   ├── mempool_monitor.rs       # Level 3 strategy
│   ├── jito_bundle.rs           # Jito integration
│   ├── executor.rs              # Trade execution
│   ├── price_fetcher.rs         # Real-time prices
│   ├── profit_calculator.rs     # Fee accounting (CRITICAL!)
│   ├── risk_manager.rs          # Safety controls
│   ├── metrics.rs               # Performance tracking
│   └── types.rs                 # Core data structures
├── DEPLOYMENT_GUIDE.md          # Complete deployment instructions
├── Cargo.toml                   # Dependencies
└── .env                         # Configuration (you create this)
```

## ⚠️ IMPORTANT - Read Before Running

### 1. Test First!
```bash
DRY_RUN=true cargo run --release
```
Run for 24-48 hours in dry-run mode before going live.

### 2. Use Premium RPC
Free public RPC will NOT work for MEV. Use:
- Triton (recommended for MEV)
- Helius (great performance)
- QuickNode (reliable)

### 3. Start Small
```env
MAX_TRADE_SIZE_SOL=0.1    # Very small to start!
MAX_DAILY_LOSS_SOL=0.1    # Tight stop loss
```

### 4. Monitor Actively
Watch logs for:
- Opportunities found
- Trades executed
- Circuit breaker triggers
- Error patterns

## 🔧 Configuration

Key environment variables in `.env`:

```env
# REQUIRED
RPC_URL=https://your-premium-rpc-url
WALLET_PRIVATE_KEY=your_base58_or_json_key

# Trading (start conservative!)
MIN_PROFIT_SOL=0.01
MIN_PROFIT_PERCENT=0.5
MAX_TRADE_SIZE_SOL=1.0
MAX_DAILY_LOSS_SOL=0.5

# Safety (keep dry run on initially!)
DRY_RUN=true
```

See `.env.mev.example` for all options.

## 💰 Profit Expectations

**Conservative Estimate:**
- Win rate: 60-70% of executed trades
- Average profit: 0.1-0.5% per trade after fees
- Opportunities: 5-20 per day (market dependent)
- Daily profit: 0.5-2% of deployed capital

**Example with 10 SOL capital:**
- ~0.13 SOL per day ($13 at $100/SOL)
- ~4 SOL per month ($400)

**Reality:**
- These are ESTIMATES, not guarantees
- Heavily dependent on market conditions
- RPC latency is critical
- Competition from other bots exists

## 📖 Documentation

- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete setup and deployment instructions
- **[MEV_BOT_STATUS.md](../MEV_BOT_STATUS.md)** - Technical implementation details

## ⚖️ Legal & Ethics

- For educational and research purposes
- MEV is legal but ethically complex
- Never use on others' private transactions
- Comply with local regulations
- DYOR (Do Your Own Research)

## 🛟 Support

If issues occur:
1. Check logs for errors
2. Review DEPLOYMENT_GUIDE.md troubleshooting section
3. Test in DRY_RUN mode
4. Start with smallest position sizes
5. Verify RPC provider is working

## ⚡ Safety Features

Built-in protections:
- ✅ Dry-run mode (default enabled)
- ✅ Trade size limits
- ✅ Daily loss limits
- ✅ Circuit breakers
- ✅ Conservative profit calculations
- ✅ Re-validation before execution
- ✅ Position exposure tracking

## 📈 Monitoring

The bot prints real-time metrics:
- Opportunities scanned/found
- Trades executed (success/failure)
- Daily P/L
- Risk metrics
- Strategy breakdown

## 🎯 Success Criteria

You'll know it's working when:
- ✅ Runs 24+ hours without crashes
- ✅ Finds opportunities regularly
- ✅ Trades execute successfully (>60% win rate)
- ✅ Daily P/L is net positive over 7 days
- ✅ Circuit breakers NOT triggering frequently

---

**Good luck and trade responsibly! 🚀**

Built with focus on safety, conservative profit calculations, and risk management.
