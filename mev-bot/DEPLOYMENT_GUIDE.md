# MEV Bot - Complete Deployment Guide

## 🚀 Production-Ready Solana MEV Bot

A complete 3-level MEV bot for Solana that executes profitable arbitrage opportunities while accounting for ALL fees and slippage.

### Features

**Level 1: Cross-DEX Arbitrage**
- Scan Jupiter, Raydium, Orca for price discrepancies
- Execute buy-low-sell-high across DEXs
- Conservative profit calculations

**Level 2: Multi-Hop Arbitrage**
- Find circular arbitrage paths (e.g., SOL → USDC → BONK → SOL)
- Support for 2-hop, 3-hop, and 4-hop paths
- Path optimization and profit maximization

**Level 3: MEV Searcher**
- Mempool monitoring for large swaps
- Back-running opportunities
- Jito bundle integration for guaranteed execution
- Liquidation scanning (planned)

**Risk Management**
- Trade size limits
- Daily loss limits with auto-pause
- Circuit breakers on consecutive failures
- Position exposure tracking
- Real-time P/L monitoring

**Profit Calculator**
- Accounts for ALL costs:
  - Transaction fees (base + priority)
  - Protocol fees (DEX-specific)
  - Slippage (both buy AND sell sides)
- Re-validates profitability before execution
- Conservative estimates to prevent "simulation-only" profits

---

## 📋 Prerequisites

### 1. System Requirements
- Linux/macOS (recommended) or Windows with WSL
- 4+ GB RAM
- Stable internet connection
- Rust 1.70+ installed

### 2. Solana Wallet
- Create a new wallet for the bot (DO NOT use your main wallet)
- Fund with SOL for trading (start small: 1-5 SOL for testing)
- Export private key as base58 string or JSON bytes

### 3. RPC Provider
**CRITICAL**: Use a premium RPC provider for production!

**Recommended providers:**
- **Triton** (triton.one) - Best for MEV, very low latency
- **Helius** (helius.xyz) - Great performance, generous free tier
- **QuickNode** (quicknode.com) - Reliable, fast

**Free RPC** (`https://api.mainnet-beta.solana.com`) will NOT work well for MEV due to:
- High latency
- Rate limits
- No priority routing

---

## 🛠️ Installation

### Step 1: Clone and Build

```bash
cd /home/user/cv/mev-bot

# Build the project
cargo build --release

# Verify compilation
cargo test
```

### Step 2: Configure Environment

```bash
# Copy example config
cp ../.env.mev.example .env

# Edit configuration
nano .env
```

### Step 3: Critical Configuration

Edit `.env` and set these values:

```env
# 1. RPC Configuration (REQUIRED)
RPC_URL=https://your-premium-rpc-url-here

# 2. Wallet Private Key (REQUIRED)
# Get from: solana-keygen export-seed-phrase
# Then convert to base58: solana-keygen pubkey wallet.json
WALLET_PRIVATE_KEY=your_base58_private_key_here

# 3. Trading Parameters
MIN_PROFIT_SOL=0.01              # Minimum 0.01 SOL profit
MIN_PROFIT_PERCENT=0.5           # Minimum 0.5% profit
MAX_TRADE_SIZE_SOL=1.0           # Start small!
MAX_DAILY_LOSS_SOL=0.5           # Stop if lose 0.5 SOL/day

# 4. Safety First!
DRY_RUN=true                     # Test mode - no real trades
```

---

## 🧪 Testing (MANDATORY BEFORE LIVE!)

### Phase 1: Dry Run Testing (24-48 hours)

```bash
# Run in dry run mode
DRY_RUN=true cargo run --release

# Monitor output for:
# - Opportunities found
# - Simulated profit calculations
# - Error rates
# - Performance metrics
```

**What to look for:**
- Are opportunities being found? (Should see some every few minutes)
- Are profit calculations reasonable? (0.5-5% typically)
- Are there any errors? (Fix before going live)
- Is the bot stable? (No crashes, memory leaks)

### Phase 2: Small Live Testing (48 hours)

```bash
# Edit .env
DRY_RUN=false
MAX_TRADE_SIZE_SOL=0.1          # Very small trades!
MAX_DAILY_LOSS_SOL=0.1          # Tight stop loss

# Run live with small amounts
cargo run --release

# Monitor closely!
# - Check wallet balance frequently
# - Verify trades on Solscan
# - Watch for unexpected behavior
```

### Phase 3: Scale Gradually

Only if Phase 2 is profitable:

```bash
# Gradually increase over days/weeks
MAX_TRADE_SIZE_SOL=0.5   # Day 3-4
MAX_TRADE_SIZE_SOL=1.0   # Day 5-7
MAX_TRADE_SIZE_SOL=2.0   # Week 2
# etc...
```

---

## 🎯 Running in Production

### Option 1: Screen/Tmux (Simple)

```bash
# Start in screen
screen -S mev-bot
cd /home/user/cv/mev-bot
cargo run --release

# Detach: Ctrl+A, D
# Reattach: screen -r mev-bot
```

### Option 2: Systemd Service (Recommended)

```bash
# Create service file
sudo nano /etc/systemd/system/mev-bot.service
```

```ini
[Unit]
Description=Solana MEV Bot
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/user/cv/mev-bot
Environment="RUST_LOG=info"
ExecStart=/home/user/.cargo/bin/cargo run --release
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable mev-bot
sudo systemctl start mev-bot

# Check status
sudo systemctl status mev-bot

# View logs
journalctl -u mev-bot -f
```

### Option 3: Docker (Advanced)

```dockerfile
FROM rust:1.70 as builder
WORKDIR /app
COPY . .
RUN cargo build --release

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y libssl-dev ca-certificates
COPY --from=builder /app/target/release/mev-bot /usr/local/bin/
CMD ["mev-bot"]
```

```bash
docker build -t mev-bot .
docker run -d --name mev-bot --env-file .env mev-bot
```

---

## 📊 Monitoring & Maintenance

### Real-Time Monitoring

The bot prints dashboard every 60 seconds showing:
- Opportunities found
- Trades executed (success/failure)
- Daily P/L
- Risk metrics
- Strategy breakdown

### Log Analysis

```bash
# View recent logs
tail -f logs/mev-bot.log

# Search for profitable trades
grep "Trade successful" logs/mev-bot.log | grep "Profit:"

# Check for errors
grep "ERROR" logs/mev-bot.log

# Monitor circuit breaker triggers
grep "CIRCUIT BREAKER" logs/mev-bot.log
```

### Health Checks

Monitor these metrics daily:
1. **Win Rate**: Should be >60% after fees
2. **Daily P/L**: Should be net positive over rolling 7 days
3. **Error Rate**: Should be <10% of trades
4. **Circuit Breakers**: Investigate if triggered frequently

---

## ⚠️ Risk Management & Safety

### Before Going Live Checklist

- [ ] Tested in DRY_RUN mode for 24+ hours
- [ ] Used premium RPC provider (not free public RPC)
- [ ] Created dedicated wallet (not main wallet)
- [ ] Started with small position sizes (<1 SOL)
- [ ] Set conservative MAX_DAILY_LOSS_SOL
- [ ] Monitoring bot output actively
- [ ] Set up alerts for circuit breaker triggers
- [ ] Backed up wallet private key securely
- [ ] Understand profit calculations and fees
- [ ] Have emergency stop plan ready

### Emergency Stop Procedure

If something goes wrong:

```bash
# 1. Stop the bot immediately
sudo systemctl stop mev-bot
# OR
pkill -9 mev-bot

# 2. Check wallet balance
solana balance <your-wallet-address>

# 3. Review recent transactions
# Visit: https://solscan.io/account/<your-wallet>

# 4. Investigate logs
grep "ERROR\|WARN" logs/mev-bot.log | tail -100

# 5. Withdraw funds if needed
solana transfer <safe-wallet> <amount> --from <bot-wallet>
```

### Common Issues & Solutions

**Issue: No opportunities found**
- Check RPC connection (is it responding?)
- Verify MIN_PROFIT_SOL isn't too high
- Check if markets are active (weekends are slower)

**Issue: All trades failing**
- Check wallet has enough SOL for fees
- Verify RPC provider isn't rate limiting
- Check network congestion (priority fee too low?)

**Issue: Simulation profits but not real**
- This is EXPECTED sometimes (prices move fast)
- If consistent: Increase MIN_PROFIT_PERCENT
- Check slippage settings (might be too optimistic)

**Issue: Circuit breaker triggered**
- GOOD - it's protecting you!
- Review recent failed trades
- Check if market conditions changed
- Resume manually only after investigation

---

## 💰 Profit Expectations

### Realistic Expectations

**Conservative estimate:**
- Win rate: 60-70% of executed trades profitable
- Average profit per trade: 0.1-0.5% after fees
- Opportunities: 5-20 per day (varies by market)
- Daily profit: 0.5-2% of deployed capital

**Example:**
- Capital: 10 SOL
- Opportunities: 10/day
- Win rate: 65%
- Avg profit: 0.2% per winning trade
- Daily profit: ~0.13 SOL ($13 at $100/SOL)
- Monthly: ~4 SOL ($400)

**Reality check:**
- These are ESTIMATES, not guarantees
- Market conditions vary greatly
- Competition from other MEV bots
- Your RPC latency matters significantly
- More capital = more opportunities (but more risk!)

### Optimization Tips

1. **Use best RPC**: Triton > Helius > QuickNode >> Public
2. **Optimize parameters**: Backtesting different MIN_PROFIT_PERCENT
3. **Monitor Level 2**: Multi-hop can be more profitable
4. **Time of day**: More volume during US/EU trading hours
5. **Network fees**: Lower during off-peak hours

---

## 🔧 Advanced Configuration

### Premium RPC Setup (Triton Example)

```env
RPC_URL=https://triton-mainnet.helius-rpc.com/?api-key=YOUR_API_KEY
WS_URL=wss://triton-mainnet.helius-rpc.com/?api-key=YOUR_API_KEY
```

### Jito MEV Bundle Setup

```env
USE_JITO_BUNDLES=true
JITO_BLOCK_ENGINE_URL=https://mainnet.block-engine.jito.wtf
```

Jito allows atomic execution of bundles (Level 3 MEV).

### Multiple Strategies

Enable/disable strategies based on performance:

```rust
// In orchestrator.rs, comment out unwanted strategies
let (level1_result, level2_result) = tokio::join!(
    self.run_level1_strategy(),
    self.run_level2_strategy(),
    // self.run_level3_strategy(),  // Disable Level 3
);
```

---

## 📈 Performance Tuning

### For Maximum Profit

```env
# Aggressive settings
SCAN_INTERVAL_MS=50              # Scan more frequently
MIN_PROFIT_SOL=0.005             # Lower threshold
MAX_TRADE_SIZE_SOL=5.0           # Larger positions
PRIORITY_FEE_MICROLAMPORTS=50000 # Higher priority
```

**Tradeoff**: Higher costs, more competition

### For Maximum Safety

```env
# Conservative settings
SCAN_INTERVAL_MS=1000            # Less aggressive
MIN_PROFIT_SOL=0.02              # Higher threshold
MAX_TRADE_SIZE_SOL=1.0           # Smaller positions
MAX_DAILY_LOSS_SOL=0.5           # Tight stop loss
```

**Tradeoff**: Fewer opportunities, less profit potential

---

## 🐛 Troubleshooting

### Compilation Errors

```bash
# Update dependencies
cargo update

# Clean build
cargo clean
cargo build --release

# Check Rust version
rustc --version  # Should be 1.70+
```

### Runtime Errors

**Error: "RPC request failed"**
- Check RPC_URL is correct
- Test connection: `curl $RPC_URL`
- Verify API key if using premium RPC

**Error: "Failed to send transaction"**
- Check wallet has enough SOL
- Network might be congested (increase priority fee)
- RPC might be down (try backup RPC)

**Error: "Opportunity no longer valid"**
- This is NORMAL - prices move fast
- If frequent: Increase SCAN_INTERVAL_MS
- Or: Improve RPC latency

---

## 📚 Additional Resources

- **Solana Docs**: https://docs.solana.com
- **Jupiter API**: https://station.jup.ag/docs
- **Jito MEV**: https://www.jito.wtf/
- **Solscan**: https://solscan.io (transaction explorer)

---

## ⚖️ Legal & Ethics

- This bot is for educational and research purposes
- MEV is legal but ethically gray area
- Never use on others' private transactions without permission
- Comply with local regulations
- DYOR (Do Your Own Research)

---

## 🎓 Learning & Improvement

### Understanding the Code

Key files to study:
1. `src/types.rs` - Core data structures
2. `src/profit_calculator.rs` - **CRITICAL** - fee calculations
3. `src/arbitrage_detector.rs` - Opportunity finding
4. `src/executor.rs` - Trade execution
5. `src/risk_manager.rs` - Safety mechanisms

### Improving Performance

Ideas for enhancement:
- Add more DEXs (Meteora, Lifinity, etc.)
- Implement flash loans for larger arbs
- Add machine learning for parameter optimization
- Build custom RPC infrastructure
- Add CEX-DEX arbitrage

---

## 📞 Support

For issues or questions:
1. Check this guide first
2. Review error logs
3. Test in DRY_RUN mode
4. Start with small positions
5. Build understanding gradually

**Remember**: This is sophisticated software. Take time to understand it before risking significant capital.

---

## 🎉 Success Metrics

You'll know it's working when:
- ✅ Bot runs for 24+ hours without crashes
- ✅ Opportunities are being found regularly
- ✅ Trades are executing successfully (>60% win rate)
- ✅ Daily P/L is net positive over rolling 7 days
- ✅ Circuit breakers NOT triggering frequently
- ✅ You understand what the bot is doing!

**Good luck and trade responsibly! 🚀**
