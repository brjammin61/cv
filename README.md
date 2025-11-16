# ORE Arbitrage Bot 🤖⚡

A high-performance, automated arbitrage system for the Solana ORE token that intelligently decides whether to mine or buy ORE based on real-time cost analysis.

## 🎯 Overview

This bot operates 24/7, continuously comparing two values:
- **Your_Breakeven_Cost**: Real-time cost (in SOL) to mine 1 ORE
- **Market_Price**: Best available price (in SOL) to buy 1 ORE on DEX

Based on a configurable profit threshold, it automatically:
- **MINES** when mining is more profitable than buying
- **BUYS** (via Jupiter DEX) when buying is more profitable than mining
- **HOLDS** when the difference is within the threshold

## 🏗️ Architecture

### Core Modules

1. **Cost Engine** (`modules/cost-engine/`)
   - Calculates real-time mining costs using dynamic priority fees
   - Queries Solana's `getRecentPrioritizationFees` RPC method
   - Factors in network congestion and ORE protocol fees (10%)
   - **This is the "secret sauce"** - dynamic cost calculation, not fixed values

2. **Price Oracle** (`modules/price-oracle/`)
   - Fetches real-time ORE prices from Jupiter V6 API
   - Provides best available swap rates
   - Includes price impact analysis

3. **Swap Executor** (`modules/swap-executor/`)
   - Executes SOL→ORE swaps via Jupiter V6
   - Handles transaction signing, sending, and confirmation
   - Implements retry logic for failed transactions
   - Supports custom priority fees

4. **Miner Control** (`modules/miner-control/`)
   - Interfaces with ORE mining clients
   - Starts/stops mining processes
   - Monitors miner health and uptime

5. **Orchestration Core** (`ore-bot/`)
   - Central decision-making engine
   - Coordinates all modules
   - Executes arbitrage strategy
   - Comprehensive logging and monitoring

## 🚀 Quick Start

### Prerequisites

- Rust 1.75+ (`curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`)
- Docker & Docker Compose (for containerized deployment)
- Solana CLI (for wallet management)
- Premium RPC endpoint (Helius, Triton, QuickNode, etc.)
- ORE mining client (e.g., official ORE CLI)

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd cv
```

2. **Create your wallet**
```bash
# Generate a new Solana keypair
solana-keygen new --outfile wallet.json

# Fund it with SOL
solana airdrop 1 wallet.json  # Devnet
# Or send SOL from another wallet for mainnet
```

3. **Configure the bot**
```bash
# Copy example config
cp .env.example .env

# Edit configuration
nano .env
```

**Critical settings to configure:**
```env
RPC_URL=https://mainnet.helius-rpc.com/?api-key=YOUR_KEY
WALLET_PATH=wallet.json
MINER_PATH=ore  # Path to your ORE miner
PROFIT_THRESHOLD_PERCENT=5.0
AUTO_EXECUTE_SWAPS=false  # Set to false for testing!
```

4. **Install the ORE miner** (if not already installed)
```bash
# Example: Install official ORE CLI
cargo install ore-cli

# Or download a pre-built binary
# Place it in your PATH or set MINER_PATH to its location
```

### Running Locally

```bash
# Build the project
cargo build --release

# Run the bot
cargo run --release --bin ore-bot

# Or run the binary directly
./target/release/ore-bot
```

### Running with Docker

```bash
# Build the Docker image
docker-compose build

# Start the bot
docker-compose up -d

# View logs
docker-compose logs -f ore-bot

# Stop the bot
docker-compose down
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `RPC_URL` | Solana RPC endpoint | - | ✅ |
| `WALLET_PATH` | Path to wallet keypair | `wallet.json` | ✅ |
| `ORE_MINT` | ORE token mint address | `oreoU2P8...` | ❌ |
| `MINER_PATH` | Path to miner executable | `ore` | ❌ |
| `MINER_ARGS` | Miner command arguments | `mine` | ❌ |
| `ESTIMATED_COMPUTE_UNITS` | Mining tx compute units | `200000` | ❌ |
| `PROFIT_THRESHOLD_PERCENT` | Profit margin threshold | `5.0` | ❌ |
| `POLL_INTERVAL_SECONDS` | Decision cycle interval | `30` | ❌ |
| `SLIPPAGE_BPS` | Swap slippage tolerance | `50` | ❌ |
| `SWAP_AMOUNT_SOL` | SOL amount per swap | `0.1` | ❌ |
| `AUTO_EXECUTE_SWAPS` | Enable auto-swapping | `false` | ❌ |

### Tuning for Optimal Performance

1. **RPC Selection**
   - Use a premium RPC with low latency (<50ms)
   - Deploy close to RPC endpoint (same region)
   - Consider dedicated RPC nodes for production

2. **Profit Threshold**
   - Lower (1-3%): More aggressive, frequent switches
   - Medium (3-7%): Balanced approach
   - Higher (7-15%): Conservative, stable operation

3. **Poll Interval**
   - Faster (10-30s): More responsive, higher API usage
   - Slower (30-120s): Less responsive, lower costs

4. **Compute Units**
   - Calibrate from actual mining transactions
   - Check Solana Explorer for your miner's CU usage
   - Update `ESTIMATED_COMPUTE_UNITS` accordingly

## 📊 How It Works

### Decision Logic

```rust
if Your_Breakeven_Cost < Market_Price - Threshold:
    SIGNAL: MINE
    ACTION: Start mining client

else if Market_Price < Your_Breakeven_Cost - Threshold:
    SIGNAL: BUY
    ACTION: Execute Jupiter swap (SOL → ORE)

else:
    SIGNAL: HOLD
    ACTION: Maintain current state
```

### Example Scenario

```
Mining Cost: 0.0095 SOL per ORE
Market Price: 0.0105 SOL per ORE
Threshold: 5%

Calculation:
- Mining is 9.5% cheaper than buying
- This exceeds the 5% threshold
- Decision: MINE ✅

The bot starts the miner and keeps it running until
market conditions change.
```

## 🔐 Security Best Practices

1. **Wallet Security**
   - Use a dedicated wallet with limited funds
   - Never commit wallet files to git
   - Rotate wallets periodically
   - Use hardware wallets for large operations

2. **RPC Security**
   - Never share your RPC API keys
   - Use authenticated endpoints
   - Monitor for unusual activity
   - Set up rate limiting

3. **Testing**
   - Start with `AUTO_EXECUTE_SWAPS=false`
   - Test on devnet first
   - Use small amounts initially
   - Monitor for 24-48 hours before scaling

4. **Monitoring**
   - Set up alerts for errors
   - Monitor wallet balance
   - Track swap execution
   - Review logs regularly

## 🐛 Troubleshooting

### Bot won't start

```bash
# Check configuration
cat .env

# Verify wallet exists
ls -la wallet.json

# Check RPC connectivity
curl -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"getHealth"}' \
  $RPC_URL
```

### Miner won't start

```bash
# Verify miner path
which ore  # or your custom miner

# Test miner manually
ore mine --keypair wallet.json

# Check miner logs
docker-compose logs -f ore-bot
```

### Swaps failing

```bash
# Check wallet balance
solana balance wallet.json

# Verify RPC is working
solana cluster-version --url $RPC_URL

# Check Jupiter API status
curl https://quote-api.jup.ag/v6/health
```

### High priority fees

```bash
# Monitor network congestion
# Adjust ESTIMATED_COMPUTE_UNITS if needed
# Consider increasing PROFIT_THRESHOLD_PERCENT
```

## 📈 Performance Optimization

### Infrastructure Recommendations

1. **Server Location**: Deploy in the same region as your RPC
2. **Server Specs**:
   - CPU: 2+ cores
   - RAM: 2GB minimum
   - Network: Low latency, high bandwidth

3. **RPC Providers** (ranked by performance):
   - Helius (best for Solana)
   - Triton
   - QuickNode
   - Alchemy

### Cost Optimization

- Tune `POLL_INTERVAL_SECONDS` to balance responsiveness vs. API costs
- Use `ESTIMATED_COMPUTE_UNITS` to avoid overpaying for priority fees
- Set `SWAP_AMOUNT_SOL` based on liquidity analysis

## 🧪 Testing

### Unit Tests

```bash
# Run all tests
cargo test

# Run specific module tests
cargo test -p cost-engine
cargo test -p price-oracle
```

### Integration Testing

```bash
# Test with dry-run mode
AUTO_EXECUTE_SWAPS=false cargo run --release

# Monitor decision-making
tail -f logs/ore-bot.log
```

## 📝 Logging

Logs include:
- Decision cycles (MINE/BUY/HOLD)
- Cost calculations
- Price quotes
- Swap executions
- Miner status
- Errors and warnings

Configure log level with `RUST_LOG`:
```bash
RUST_LOG=debug  # Very verbose
RUST_LOG=info   # Normal operation (recommended)
RUST_LOG=warn   # Only warnings and errors
```

## 🛣️ Roadmap

- [ ] Add production-ready `getRecentPrioritizationFees` implementation
- [ ] Implement Prometheus metrics export
- [ ] Add Grafana dashboards
- [ ] Support multiple DEXs (Raydium, Orca)
- [ ] Add Telegram/Discord alerts
- [ ] Implement profit/loss tracking
- [ ] Add backtesting framework
- [ ] Support multiple token pairs

## ⚖️ Legal & Compliance

**IMPORTANT**: This is a market efficiency and arbitrage tool. All activities must be:

✅ **Legal and Compliant**
- Operates within Solana network terms of service
- Uses public APIs (Jupiter, RPC)
- No network-abusive behavior
- Complies with local regulations

❌ **Do NOT Use For**
- Market manipulation
- Flash loan attacks
- Excessive RPC abuse
- Violating exchange terms of service

**Disclaimer**: Use at your own risk. The authors are not responsible for financial losses, security breaches, or any damages resulting from using this software.

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- Solana Foundation
- Jupiter Exchange
- ORE Protocol Team
- Rust Community

## 📞 Support

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Security**: Report vulnerabilities privately

---

**⚡ Built with Rust for maximum performance on Solana ⚡**

*For questions about implementation, ORE mining, or arbitrage strategies, please open a GitHub issue.*
