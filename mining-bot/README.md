# 🪨 Project IronPick: Solana Mining Profitability Bot

An automated, high-frequency profitability engine for mining ORE and COAL on Solana. This bot continuously calculates real-time profitability and automatically switches mining targets to maximize profits or stops mining when unprofitable.

## 📋 Overview

Project IronPick solves the core problem of manual mining: **unprofitability during unfavorable market conditions**. The 60-second "epoch" system and Solana's priority fee wars mean that mining during non-profitable windows results in guaranteed losses.

This bot acts as an economic advisor that:
- ✅ Prevents losses by stopping mining when unprofitable
- ✅ Captures momentary arbitrage opportunities
- ✅ Automatically switches between ORE and COAL mining
- ✅ Optimizes for real-time market conditions

## 🏗️ Architecture

The bot runs in a 60-second loop with four key steps:

1. **Hardware Benchmark**: Measures local hashrate (Hashes Per Minute) using the drillx algorithm
2. **On-Chain Survey**: Fetches global difficulty, reward rates, and priority fees from ORE/COAL programs
3. **Market Analysis**: Fetches real-time USDC prices for ORE, COAL, and SOL from Jupiter
4. **Profitability Calculation**: Calculates net profit and issues mining commands (MINE ORE, MINE COAL, or SLEEP)

## 🚀 Quick Start

### Prerequisites

1. **Rust** (1.70+)
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   ```

2. **ore-cli** (ORE mining CLI)
   ```bash
   cargo install ore-cli
   ```

3. **coal-cli** (COAL mining CLI)
   ```bash
   cargo install coal-cli
   ```

4. **Solana CLI** with configured keypair
   ```bash
   solana-keygen new
   ```

### Installation

1. Clone and navigate to the project:
   ```bash
   cd mining-bot
   ```

2. Build the project:
   ```bash
   cargo build --release
   ```

3. Copy and configure the settings:
   ```bash
   cp config.example.json config.json
   # Edit config.json with your settings
   ```

### Configuration

Edit `config.json` with your settings:

```json
{
  "rpc": {
    "url": "YOUR_PREMIUM_RPC_URL",  // Use a private RPC for best performance
    "timeout_secs": 30
  },
  "miner": {
    "keypair_path": "/path/to/your/keypair.json",
    "thread_count": 8,              // Adjust based on your CPU
    "ore_cli_path": "ore",
    "coal_cli_path": "coal"
  },
  "energy": {
    "hardware_watts": 50.0,         // Your hardware power consumption
    "electricity_cost_kwh": 0.10    // Your electricity cost per kWh
  },
  "mining": {
    "staking_multiplier": 1.5,      // Your ORE staking multiplier
    "benchmark_duration_secs": 60,
    "epoch_duration_secs": 60
  }
}
```

### Running

```bash
cargo run --release
```

Or run the compiled binary:
```bash
./target/release/solana-mining-advisor
```

## ⚙️ How It Works

### Profitability Calculation

For each asset (ORE and COAL), the bot calculates:

**Gross Revenue:**
```
expected_reward_per_min = (local_hashrate / global_difficulty) × reward_rate × staking_multiplier
gross_revenue = expected_reward_per_min × token_price_usd
```

**Operational Costs:**
```
tx_fee_cost = (base_fee + priority_fee) × sol_price_usd
energy_cost = (hardware_watts / 1000) × (electricity_cost_kwh / 60)
operational_cost = tx_fee_cost + energy_cost
```

**Net Profit:**
```
net_profit = gross_revenue - operational_cost
```

### Decision Logic

The bot makes decisions based on profitability:

1. **MINE ORE**: If ORE is profitable and more profitable than COAL
2. **MINE COAL**: If COAL is profitable and more profitable than ORE
3. **SLEEP**: If neither asset is profitable

When switching targets, the bot:
- Kills the current mining process
- Starts a new process with the optimal priority fee
- Continues monitoring in the background

## 🔧 Advanced Configuration

### Using a Premium RPC

For best results, use a premium RPC provider like:
- Helius (https://helius.dev)
- QuickNode (https://quicknode.com)
- Triton (https://triton.one)

Public RPCs may fail during high-traffic periods.

### Optimizing Thread Count

```bash
# Check your CPU cores
nproc

# Set thread_count in config.json to match
```

### Custom Mining CLIs

If ore-cli and coal-cli are not in your PATH:

```json
{
  "miner": {
    "ore_cli_path": "/full/path/to/ore",
    "coal_cli_path": "/full/path/to/coal"
  }
}
```

## 📊 Sample Output

```
╔════════════════════════════════════════════════════════════╗
║        🪨 PROJECT IRONPICK: SOLANA MINING ADVISOR 🪨       ║
║                                                            ║
║  Automated profitability engine for ORE and COAL mining   ║
╚════════════════════════════════════════════════════════════╝

⚙️  Configuration loaded:
   RPC: https://mainnet.helius-rpc.com/?api-key=xxx
   Staking Multiplier: 1.5
   Hardware: 50W @ $0.1/kWh

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  🎯 RECOMMENDATION: MINE ORE                    ┃
┃  ✅ Profit: $0.005995/min                       ┃
┃     ($0.36/hour, $8.63/day)                     ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

🔄 Switching mining target: SLEEP → ORE
  ▶️  Starting ORE miner...
  ✅ ORE miner started (PID: 12345)
```

## 🛠️ Development Tasks

### Critical TODOs

This project has three key areas that need implementation:

#### 1. Find On-Chain State Accounts (HIGHEST PRIORITY)

The code currently uses mock data for `global_difficulty` and `reward_rate`. You need to:

- Find the actual Pubkeys for ORE Treasury and COAL Config accounts
- Use `RpcClient::get_program_accounts` with the known Program IDs
- Reference ore-cli and coal-cli GitHub repos for the correct struct definitions
- Update `src/onchain.rs` with the real account addresses

**Program IDs:**
- ORE: `oreoU2P8bN6jkk3jbaiVxYnG1dCXcYxwhwyK9jSybcp`
- COAL: `E3yUqBNTZxV8ELvW99oRLC7z4ddbJqqR4NphwrMug9zu`

#### 2. Verify drillx Implementation

The hardware benchmark uses the `drillx` crate (v2.0.0). Verify that:
- The benchmark accurately measures your hardware
- The hash function matches what ore-cli/coal-cli use
- Multi-threading is working correctly

#### 3. Fine-Tune Energy Costs

Update `config.json` with your actual:
- Hardware power consumption (use a power meter)
- Local electricity costs
- Any additional operational costs

### Optional Enhancements

- [ ] Add configuration file support (currently uses hardcoded defaults)
- [ ] Implement logging to file
- [ ] Add Prometheus metrics export
- [ ] Create systemd service file for auto-start
- [ ] Add Discord/Telegram notifications
- [ ] Implement automatic RPC failover
- [ ] Add historical profitability tracking

## 🐛 Troubleshooting

### "Failed to start ore-cli/coal-cli"

Ensure the CLIs are installed and in PATH:
```bash
which ore
which coal
```

### "Failed to connect to RPC"

- Check your internet connection
- Verify RPC URL is correct
- Try a different RPC provider

### "Mock on-chain data" warning

This is expected until you implement the real state account fetching (see Development Tasks above).

### Mining not profitable

This is normal! The bot is designed to sleep when mining isn't profitable. Wait for better market conditions.

## 📈 Performance Tips

1. **Use a premium RPC** - Public RPCs are too slow for competitive mining
2. **Optimize thread count** - Match your CPU core count
3. **Monitor energy costs** - Ensure they're accurately configured
4. **Check staking multiplier** - Update based on your actual ORE staking
5. **Run on dedicated hardware** - Competing processes will reduce hashrate

## 🔒 Security

- Never commit your `config.json` with real keypair paths
- Use a dedicated mining wallet with limited funds
- Monitor the bot's transactions regularly
- Keep your RPC URL private (especially if it has an API key)

## 📜 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📞 Support

For issues and questions:
- Open a GitHub issue
- Check the troubleshooting section above
- Review the ORE and COAL documentation

## ⚠️ Disclaimer

This bot is provided as-is. Cryptocurrency mining carries risks including:
- Financial loss from unprofitable mining
- Hardware wear and tear
- Electricity costs
- Smart contract risks

Always test with small amounts first and monitor your bot closely.

---

**Built with 🪨 for the Solana mining community**
