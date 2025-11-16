# Quick Start Guide - ORE Arbitrage Bot

This guide will get you up and running in under 5 minutes.

## Prerequisites

Before you begin, ensure you have:
- ✅ Rust installed (`curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`)
- ✅ A Solana RPC endpoint (get one from [Helius](https://helius.dev), [QuickNode](https://quicknode.com), or use public RPC for testing)
- ✅ A wallet with some SOL

## 🚀 5-Minute Setup

### 1. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit the configuration
nano .env
```

**Minimum required configuration:**
```env
RPC_URL=https://api.mainnet-beta.solana.com  # Or your premium RPC
WALLET_PATH=wallet.json
AUTO_EXECUTE_SWAPS=false  # IMPORTANT: Keep false for testing!
```

### 2. Create or Import Wallet

**Option A: Create New Wallet**
```bash
solana-keygen new --outfile wallet.json
```

**Option B: Use Existing Wallet**
```bash
# Copy your existing wallet keypair to wallet.json
cp ~/.config/solana/id.json wallet.json
```

⚠️ **Security Note**: Use a dedicated wallet with limited funds for the bot!

### 3. Build the Bot

```bash
cargo build --release
```

This will take a few minutes the first time.

### 4. Run the Bot

```bash
./target/release/ore-bot
```

You should see output like:
```
INFO ORE Arbitrage Bot starting...
INFO Wallet loaded: <your-public-key>
INFO Bot initialized successfully
INFO Starting ORE Arbitrage Bot main loop...
INFO === Starting decision cycle ===
INFO Mining breakeven cost: 0.0095 SOL
INFO Market price: 0.0105 SOL
INFO Mining is 9.5% cheaper than buying - MINE
```

## 🛠️ Troubleshooting

### "RPC_URL not set"
Make sure you copied `.env.example` to `.env` and set the RPC_URL

### "Failed to read wallet file"
Ensure `wallet.json` exists and is a valid Solana keypair

### Build errors
Try updating Rust: `rustup update stable`

## 📊 Understanding the Output

The bot will continuously:
1. **Calculate mining cost** - Real-time cost to mine 1 ORE
2. **Fetch market price** - Current DEX price for 1 ORE
3. **Make decision** - MINE, BUY, or HOLD
4. **Execute action** - Start miner or execute swap

Example decision cycle:
```
=== Starting decision cycle ===
Mining breakeven cost: 0.0095 SOL
Market price: 0.0105 SOL
Decision: Mine
Switching to MINING mode
Miner started successfully
=== Decision cycle complete ===
```

## ⚙️ Next Steps

### Enable Auto-Swapping (Production)

Once you've tested and are comfortable:

1. Edit `.env`:
```env
AUTO_EXECUTE_SWAPS=true
```

2. Restart the bot

### Tune Performance

Adjust these settings in `.env`:
- `PROFIT_THRESHOLD_PERCENT` - How much profit margin before switching (default: 5%)
- `POLL_INTERVAL_SECONDS` - How often to check prices (default: 30s)
- `SWAP_AMOUNT_SOL` - How much SOL to swap per buy cycle (default: 0.1)

### Install ORE Miner

The bot controls an external ORE miner. Install one:

```bash
# Official ORE CLI
cargo install ore-cli

# Or download a pre-built binary and update .env:
MINER_PATH=/path/to/your/ore-miner
```

## 🐳 Docker Deployment

For production deployment:

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## 📖 Full Documentation

For complete documentation, see [README.md](./README.md)

## 🆘 Getting Help

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Documentation**: See [README.md](./README.md)

## ⚠️ Important Reminders

- ✅ Start with `AUTO_EXECUTE_SWAPS=false`
- ✅ Use a dedicated wallet with limited funds
- ✅ Test on devnet first if possible
- ✅ Monitor the bot regularly
- ✅ Use a premium RPC for production
- ✅ Keep your wallet secure

---

**You're all set! The bot is now running and will automatically arbitrage between mining and buying ORE. 🚀**
