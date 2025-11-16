# Project IronPick Deployment Guide

## Quick Start Checklist

### Prerequisites Installed
- [x] Rust toolchain
- [x] Git
- [x] mining-bot project files
- [ ] ore-cli (installing...)
- [ ] coal-cli (pending)
- [ ] Solana CLI with funded wallet

### Configuration Steps

#### 1. Set Up Solana Wallet

```bash
# Install Solana CLI if not already installed
sh -c "$(curl -sSfL https://release.solana.com/stable/install)"

# Create a new keypair (or use existing)
solana-keygen new --outfile ~/.config/solana/id.json

# Check your wallet address
solana address

# Fund your wallet with SOL
# You need ~0.1 SOL to start (for transaction fees and account creation)
# Get SOL from an exchange or use Solana faucet for devnet testing
```

#### 2. Get a Premium RPC Endpoint

The public Solana RPC is too slow and rate-limited for competitive mining. Get a premium RPC from:

**Recommended Providers:**
- **Helius** (https://helius.dev) - Free tier available, great for mining
- **QuickNode** (https://quicknode.com) - Reliable, good performance
- **Triton** (https://triton.one) - Specialized for mining

**Sign up and get your RPC URL:**
1. Create an account
2. Create a new API endpoint for Solana Mainnet
3. Copy the RPC URL (looks like: `https://rpc.helius.xyz/?api-key=YOUR_KEY`)

#### 3. Configure the Bot

Edit `config.json`:

```json
{
  "rpc": {
    "url": "https://rpc.helius.xyz/?api-key=YOUR_KEY_HERE",
    "timeout_secs": 30
  },
  "miner": {
    "keypair_path": "/home/user/.config/solana/id.json",
    "thread_count": 8,
    "ore_cli_path": "ore",
    "coal_cli_path": "coal"
  },
  "energy": {
    "hardware_watts": 50.0,
    "electricity_cost_kwh": 0.10
  },
  "mining": {
    "staking_multiplier": 1.0,
    "benchmark_duration_secs": 60,
    "epoch_duration_secs": 60
  }
}
```

**Important Configuration Notes:**

- `rpc.url`: Replace with your premium RPC URL
- `miner.keypair_path`: Absolute path to your Solana keypair file
- `miner.thread_count`: Set to your CPU core count (check with `nproc`)
- `energy.hardware_watts`: Measure with a power meter for accuracy
- `energy.electricity_cost_kwh`: Your local electricity rate
- `mining.staking_multiplier`: Set to 1.0 initially, increase if you're staking ORE

#### 4. Verify Installations

```bash
# Check ore-cli installation
ore --version

# Check coal-cli installation
coal --version

# Check Solana CLI
solana --version

# Check your SOL balance
solana balance
```

#### 5. Create Mining Proof Accounts

Before mining, you need to initialize proof accounts:

```bash
# Initialize ORE proof account
ore \
  --rpc https://your-rpc-url \
  --keypair ~/.config/solana/id.json \
  --priority-fee 10000 \
  open

# Initialize COAL proof account
coal \
  --rpc https://your-rpc-url \
  --keypair ~/.config/solana/id.json \
  --priority-fee 10000 \
  open
```

**Note:** This costs ~0.002-0.01 SOL per account for rent. It's a one-time cost.

### Running the Bot

#### Development Mode (with logs)

```bash
cd /home/user/cv/mining-bot
RUST_LOG=info cargo run --release
```

#### Production Mode

```bash
cd /home/user/cv/mining-bot
./target/release/solana-mining-advisor
```

#### Running as a Background Service (systemd)

Create `/etc/systemd/system/mining-bot.service`:

```ini
[Unit]
Description=Project IronPick Mining Bot
After=network.target

[Service]
Type=simple
User=user
WorkingDirectory=/home/user/cv/mining-bot
ExecStart=/home/user/cv/mining-bot/target/release/solana-mining-advisor
Restart=always
RestartSec=10
Environment="RUST_LOG=info"

[Install]
WantedBy=multi-user.target
```

Then:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable autostart
sudo systemctl enable mining-bot

# Start the service
sudo systemctl start mining-bot

# Check status
sudo systemctl status mining-bot

# View logs
journalctl -u mining-bot -f
```

## Monitoring and Optimization

### Monitor Performance

The bot outputs detailed reports every 60 seconds:

```
📊 ORE PROFITABILITY REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Expected Reward: 0.000245000 ORE/min
  Gross Revenue:   $0.008234/min
  ─────────────────────────────
  Costs:
    TX Fees:       $0.002156/min
    Energy:        $0.000083/min
  Total Cost:      $0.002239/min
  ─────────────────────────────
  ✅ NET PROFIT:   $0.005995/min
     ($0.36/hour, $8.63/day)
```

### Optimization Tips

1. **Thread Count**
   - Set to your CPU core count: `nproc`
   - Try varying ±1-2 cores to find optimal performance
   - More threads = higher hashrate but also higher power consumption

2. **Staking Multiplier**
   - If you stake ORE, update `mining.staking_multiplier`
   - Check your staking tier on the ORE platform
   - Common values: 1.0 (no stake), 1.5, 2.0, 5.0

3. **Priority Fees**
   - The bot automatically sets optimal priority fees
   - During high congestion, fees spike - bot will sleep if unprofitable
   - Monitor your transaction success rate on Solscan

4. **Energy Costs**
   - Use a power meter to measure actual consumption
   - Mining is often only profitable with cheap electricity (<$0.15/kWh)
   - Consider running during off-peak hours if you have time-of-use pricing

5. **RPC Performance**
   - If you see RPC errors, upgrade to a better tier
   - Monitor RPC latency - lower is better
   - Consider running your own validator if mining at scale

## Troubleshooting

### "Failed to fetch CONFIG account"

This is expected on first run. The bot uses estimated difficulty/rewards. To fix:
1. Check you're using the correct RPC URL
2. Verify the ORE/COAL programs are deployed on mainnet
3. See README.md "Development Tasks" for implementing exact account parsing

### "Mining is not profitable"

This is normal! The bot correctly identifies when mining would lose money:
- High priority fees (congestion)
- Low token prices
- High difficulty
- High electricity costs

Wait for better conditions or adjust your energy config.

### "Failed to start ore-cli/coal-cli"

Verify the CLIs are installed and in PATH:
```bash
which ore
which coal
```

If not in PATH, update config.json with absolute paths:
```json
{
  "miner": {
    "ore_cli_path": "/home/user/.cargo/bin/ore",
    "coal_cli_path": "/home/user/.cargo/bin/coal"
  }
}
```

### Bot stops mining frequently

This is correct behavior! The bot:
- Stops when unprofitable (saves you money)
- Switches between ORE and COAL based on profitability
- Sleeps during high fee periods

### RPC connection errors

- Check your RPC URL is correct
- Verify your RPC tier has enough requests/second
- Try a different RPC provider
- Check your internet connection

## Safety and Best Practices

### Security

- **Never** commit your `config.json` with real keypair paths
- Use a dedicated mining wallet with limited funds
- Keep your RPC API key secret
- Monitor your wallet regularly

### Financial

- Start with small amounts to test
- Monitor profitability closely for the first 24 hours
- Remember: Past profitability doesn't guarantee future returns
- Set up alerts for unusual activity

### Hardware

- Monitor CPU temperature
- Ensure adequate cooling
- Mining will wear your hardware faster
- Consider hardware depreciation in profitability calculations

## Support and Resources

- ORE Documentation: https://ore.supply/docs
- COAL/Minechain: https://minechain.gg
- Solana Docs: https://docs.solana.com
- Project Issues: Check the GitHub repository

## Advanced: Updating On-Chain Data Parsing

The bot currently uses estimated difficulty/rewards. For exact data:

1. Add proper Borsh structs (see src/onchain.rs comments)
2. Reference ore source: https://github.com/regolith-labs/ore
3. Reference coal source: https://github.com/coal-digital/coal
4. Deserialize CONFIG and BUS accounts
5. Test thoroughly before deploying

This requires Rust knowledge and understanding of Solana account layouts.

---

**Good luck mining! May your hashes be profitable! 🪨⛏️**
