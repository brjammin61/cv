# Complete Setup Guide - From Absolute Zero

This guide assumes you have NOTHING installed and takes you through every step.

## What You're Building

An automated bot that:
1. Monitors the cost to mine ORE vs the cost to buy ORE
2. Automatically mines when mining is cheaper
3. Automatically buys when buying is cheaper
4. Runs 24/7 on autopilot

## Prerequisites (What You Need)

### Required:
- A computer running Linux, macOS, or Windows (WSL)
- At least 2GB RAM and 10GB disk space
- A Solana wallet with some SOL (~0.5-1 SOL to start)
- An RPC endpoint (free tier works for testing)

### Estimated Cost:
- **Testing**: Free (use public RPC + small SOL amount)
- **Production**: $50-200/month (premium RPC + server costs)

---

## STEP 0: Install System Requirements

### A) Install Rust

```bash
# Install Rust (required to build the bot)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Follow the prompts, then restart your terminal or run:
source $HOME/.cargo/env

# Verify installation
rustc --version  # Should show: rustc 1.75.0 or higher
cargo --version  # Should show: cargo 1.75.0 or higher
```

### B) Install Solana CLI

```bash
# Install Solana CLI (needed for wallet management)
sh -c "$(curl -sSfL https://release.solana.com/stable/install)"

# Add to PATH (add this to your ~/.bashrc or ~/.zshrc)
export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"

# Restart terminal or source your config, then verify:
solana --version  # Should show: solana-cli 1.18.0 or higher
```

### C) Install Docker (Optional - for containerized deployment)

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER  # Add your user to docker group
# Log out and back in for this to take effect

# Verify
docker --version
docker-compose --version
```

---

## STEP 1: Get the Bot Code

```bash
# Clone the repository (replace with your actual repo URL)
git clone https://github.com/brjammin61/cv.git
cd cv

# Verify you have all the files
ls -la
# You should see: Cargo.toml, ore-bot/, modules/, docker-compose.yml, etc.
```

---

## STEP 2: Set Up Your Wallet

You have two options:

### Option A: Create a New Wallet (Recommended for Testing)

```bash
# Create a new wallet
solana-keygen new --outfile wallet.json

# SAVE THE SEED PHRASE IT SHOWS YOU!
# You'll need this to recover your wallet if something goes wrong

# Check your wallet address
solana-keygen pubkey wallet.json
# This shows your public wallet address
```

### Option B: Use Existing Wallet

```bash
# If you already have a Solana wallet, copy it
cp ~/.config/solana/id.json wallet.json

# Or if you have a seed phrase, recover it:
solana-keygen recover --outfile wallet.json
# Then enter your seed phrase when prompted
```

### Fund Your Wallet

You need SOL to:
- Pay for transactions when buying ORE
- Pay for mining transaction fees

```bash
# Check balance
solana balance wallet.json

# For DEVNET testing (free, fake SOL):
solana config set --url devnet
solana airdrop 2 wallet.json

# For MAINNET (real money):
# Send SOL from another wallet or exchange to your address
# Get your address with: solana-keygen pubkey wallet.json
# Start with 0.5-1 SOL for testing
```

⚠️ **IMPORTANT**: Use a DEDICATED wallet for the bot, not your main wallet!

---

## STEP 3: Get an RPC Endpoint

The bot needs to talk to the Solana blockchain. You need an RPC URL.

### Free Options (Testing Only):
```bash
# Public Solana RPC (slow, rate limited)
RPC_URL=https://api.mainnet-beta.solana.com
```

### Recommended for Production:

**Helius** (Best for Solana):
1. Go to https://helius.dev
2. Sign up for free account
3. Create a new project
4. Copy your RPC URL (looks like: https://mainnet.helius-rpc.com/?api-key=YOUR_KEY)

**QuickNode**:
1. Go to https://quicknode.com
2. Sign up, create Solana endpoint
3. Copy your HTTP endpoint

**Other options**: Triton, Alchemy, GetBlock

---

## STEP 4: Install ORE Miner

The bot CONTROLS a miner, but doesn't mine itself. You need to install an ORE miner.

### Option A: Official ORE CLI (Recommended)

```bash
# Install the official ORE miner
cargo install ore-cli

# Verify installation
ore --version

# Test that it works
ore --help
```

### Option B: Download Pre-built Binary

```bash
# Check the ORE project for releases
# Download and place in your PATH or note the location
```

---

## STEP 5: Configure the Bot

```bash
# Copy the example configuration
cp .env.example .env

# Edit the configuration
nano .env  # or use your favorite editor
```

**Minimum Configuration for Testing:**

```env
# REQUIRED: Your RPC endpoint
RPC_URL=https://api.mainnet-beta.solana.com

# REQUIRED: Path to your wallet
WALLET_PATH=wallet.json

# ORE miner settings
MINER_PATH=ore  # If installed via cargo, just "ore"
MINER_ARGS=mine --keypair wallet.json

# Bot behavior
PROFIT_THRESHOLD_PERCENT=5.0
POLL_INTERVAL_SECONDS=30

# IMPORTANT: Start with this FALSE to test!
AUTO_EXECUTE_SWAPS=false

# Swap settings
SWAP_AMOUNT_SOL=0.1
SLIPPAGE_BPS=50
```

**For Production (after testing):**

```env
# Use your premium RPC
RPC_URL=https://mainnet.helius-rpc.com/?api-key=YOUR_API_KEY

# Enable auto-swaps
AUTO_EXECUTE_SWAPS=true

# Increase swap amount if desired
SWAP_AMOUNT_SOL=0.5
```

---

## STEP 6: Build the Bot

```bash
# Build in release mode (optimized, fast)
cargo build --release

# This will take 5-10 minutes the first time
# You'll see lots of "Compiling..." messages - this is normal

# Verify the build succeeded
ls -lh target/release/ore-bot
# Should show a binary file
```

---

## STEP 7: Test Run (Dry Mode)

Before running for real, test it:

```bash
# Make sure AUTO_EXECUTE_SWAPS=false in .env
grep AUTO_EXECUTE_SWAPS .env
# Should show: AUTO_EXECUTE_SWAPS=false

# Run the bot
./target/release/ore-bot
```

**What You Should See:**

```
INFO ORE Arbitrage Bot starting...
INFO Wallet loaded: YOUR_WALLET_ADDRESS_HERE
INFO Bot initialized successfully
INFO Starting ORE Arbitrage Bot main loop...
INFO Profit threshold: 5%
INFO Poll interval: 30s
INFO === Starting decision cycle ===
INFO Calculating real-time mining cost...
INFO Mining breakeven cost: 0.0095 SOL
INFO Fetching ORE price from Jupiter V6...
INFO ORE price: 0.0105 SOL (via Raydium, impact: 0.0001%)
INFO Mining is 9.5% cheaper than buying - MINE
INFO Decision: Mine
INFO Switching to MINING mode
INFO Starting miner: ore ["mine", "--keypair", "wallet.json"]
INFO Miner process started with PID: 12345
INFO Miner started successfully
INFO === Decision cycle complete ===
```

**Let it run for a few cycles (1-2 minutes) to see the decision-making:**
- It will calculate costs
- It will fetch prices
- It will decide: MINE or BUY or HOLD
- It will start/stop the miner
- With AUTO_EXECUTE_SWAPS=false, it won't actually buy, just log what it would do

Press `Ctrl+C` to stop.

---

## STEP 8: Go Live (Set and Forget)

Once you're comfortable with how it works:

### 1. Enable Auto-Swaps

```bash
nano .env
# Change: AUTO_EXECUTE_SWAPS=true
```

### 2. Start the Bot

**Option A: Run Directly**
```bash
# Run in foreground
./target/release/ore-bot

# Or run in background with nohup
nohup ./target/release/ore-bot > bot.log 2>&1 &

# Check it's running
tail -f bot.log
```

**Option B: Use Docker (Recommended for Production)**
```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f ore-bot

# Check status
docker-compose ps

# Stop
docker-compose down
```

**Option C: Use systemd (Run as Service)**
```bash
# Create a systemd service file
sudo nano /etc/systemd/system/ore-bot.service

# Add this content:
[Unit]
Description=ORE Arbitrage Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/cv
ExecStart=/path/to/cv/target/release/ore-bot
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

# Enable and start
sudo systemctl enable ore-bot
sudo systemctl start ore-bot

# Check status
sudo systemctl status ore-bot

# View logs
sudo journalctl -u ore-bot -f
```

---

## STEP 9: Monitor and Maintain

### Check the Bot is Working

```bash
# If using Docker:
docker-compose logs -f ore-bot

# If running directly:
tail -f bot.log

# If using systemd:
sudo journalctl -u ore-bot -f
```

### Monitor Your Wallet

```bash
# Check balance
solana balance wallet.json

# View transaction history
solana transaction-history $(solana-keygen pubkey wallet.json)
```

### Key Things to Monitor:

1. **Decision cycles**: Should complete every 30 seconds (or your POLL_INTERVAL)
2. **Miner status**: Should start/stop based on profitability
3. **Swap executions**: Should only happen when buying is more profitable
4. **Errors**: Watch for RPC errors, failed transactions, etc.

### Common Issues:

**"Miner failed to start"**
```bash
# Test miner manually
ore mine --keypair wallet.json
# If this fails, the miner itself has an issue
```

**"Jupiter API error"**
```bash
# ORE might not have liquidity on Jupiter yet
# Check: https://jup.ag/ and search for ORE
```

**"RPC rate limited"**
```bash
# You're hitting rate limits
# Solution: Get a premium RPC endpoint (Helius, QuickNode)
```

---

## STEP 10: Optimize for Profit

After running for 24-48 hours, tune these settings:

### Adjust Profit Threshold

```env
# More aggressive (switches strategies more often)
PROFIT_THRESHOLD_PERCENT=2.0

# More conservative (only switches for big differences)
PROFIT_THRESHOLD_PERCENT=10.0
```

### Adjust Poll Interval

```env
# Faster (more responsive, more RPC calls)
POLL_INTERVAL_SECONDS=15

# Slower (less responsive, fewer RPC calls)
POLL_INTERVAL_SECONDS=60
```

### Adjust Swap Amount

```env
# Smaller swaps (less capital at risk)
SWAP_AMOUNT_SOL=0.05

# Larger swaps (more capital deployed)
SWAP_AMOUNT_SOL=1.0
```

---

## Summary: Your Set-and-Forget Checklist

- [✓] Rust and Solana CLI installed
- [✓] Wallet created and funded with SOL
- [✓] RPC endpoint configured
- [✓] ORE miner installed
- [✓] Bot configured (.env file)
- [✓] Bot built successfully
- [✓] Tested in dry mode (AUTO_EXECUTE_SWAPS=false)
- [✓] Enabled auto-swaps (AUTO_EXECUTE_SWAPS=true)
- [✓] Bot running (Docker/systemd/background)
- [✓] Monitoring set up

**Once all checkboxes are ticked, the bot will:**
- ✅ Monitor mining vs buying costs 24/7
- ✅ Automatically start mining when profitable
- ✅ Automatically buy ORE when cheaper than mining
- ✅ Require zero intervention

---

## Emergency Commands

**Stop Everything Immediately:**
```bash
# Kill the bot
pkill ore-bot

# Kill any miners
pkill ore

# Or if using Docker:
docker-compose down
```

**Check Wallet Balance:**
```bash
solana balance wallet.json
```

**View Recent Transactions:**
```bash
solana transaction-history $(solana-keygen pubkey wallet.json) | head -20
```

---

## Getting Help

If something doesn't work:

1. **Check the logs** - errors are usually descriptive
2. **Test components individually**:
   - Can you mine manually? `ore mine --keypair wallet.json`
   - Can you query RPC? `curl -X POST $RPC_URL -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":1,"method":"getHealth"}'`
   - Is your wallet funded? `solana balance wallet.json`

3. **Common fixes**:
   - Restart the bot
   - Update RPC endpoint
   - Increase gas/priority fees
   - Add more SOL to wallet

---

**You're all set! Let it run and check back periodically. The bot will handle everything else. 🚀**
