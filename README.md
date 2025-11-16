# ORE V2 Dominance Bot

An institutional-grade, high-performance mining and arbitrage bot for the ORE V2 protocol on Solana.

## 🎯 Overview

This bot is designed to systematically exploit the ORE V2 protocol mechanics by combining:

- **High-Performance Computing**: GPU-optimized Drillx solver (10-20% faster than CPU)
- **Game Theory**: Real-time 5x5 Grid strategist with EV calculation
- **MEV Execution**: Jito bundles for guaranteed, last-second "snipe" execution
- **Information Asymmetry**: Mempool monitoring for predictive "Shadow Board"

The goal is to achieve market dominance by outperforming casual users and basic scripts through systematic exploitation of the PvP Grid system.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     ORE V2 DOMINANCE BOT                     │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Miner 1    │     │   Miner 2    │     │   Miner N    │
│  (GPU/CUDA)  │────▶│  (GPU/CUDA)  │────▶│  (GPU/CUDA)  │
└──────────────┘     └──────────────┘     └──────────────┘
        │                   │                     │
        └───────────────────┴─────────────────────┘
                           │
                    [Redis Queue]
                           │
                           ▼
              ┌────────────────────────┐
              │   Bus/Dispatcher       │
              │  (Central Orchestrator)│
              └────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│State Monitor │  │  Strategist  │  │Jito Executor │
│ (WebSocket)  │  │(EV Calculator)│  │(MEV Bundles) │
└──────────────┘  └──────────────┘  └──────────────┘
        │                  │                  │
        └──────────────────┴──────────────────┘
                           │
                           ▼
                  ┌────────────────┐
                  │  ORE V2 Grid   │
                  │  (On-Chain)    │
                  └────────────────┘
```

### Components

1. **Miners** (`ore-miner`): GPU workers that solve Drillx hashes
2. **Bus** (`ore-bus`): Central orchestrator that makes strategic decisions
3. **Strategist** (`ore-strategist`): EV calculator and game theory engine
4. **State Monitor** (`ore-state-monitor`): Real-time grid state tracking
5. **Jito Integration** (`ore-jito`): MEV execution and mempool monitoring
6. **Treasury** (`ore-treasury`): Automated staking and profit management

## 🚀 Quick Start

### Prerequisites

- **Rust** 1.75+ ([Install](https://rustup.rs/))
- **Docker** & **Docker Compose**
- **NVIDIA GPU** with CUDA 12.2+ (optional but recommended)
- **Solana CLI** ([Install](https://docs.solana.com/cli/install-solana-cli-tools))
- **Redis** (or use Docker Compose)

### Installation

```bash
# 1. Clone the repository
git clone <repository-url>
cd ore-v2-dominance-bot

# 2. Run setup script
./deployment/scripts/setup.sh

# 3. Edit configuration
nano .env

# 4. Fund your wallet
# Send SOL to the address shown during setup

# 5. Start the bot
./deployment/scripts/start.sh
```

## ⚙️ Configuration

Key environment variables in `.env`:

```bash
# Network
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
JITO_BLOCK_ENGINE_URL=https://mainnet.block-engine.jito.wtf/api/v1/bundles

# Bot Settings
MAX_STAKE_PER_ROUND=1000000000  # 1 SOL
ENABLE_MEMPOOL_MONITORING=true

# GPU Settings
ORE_MINER_GPU_ENABLED=true
ORE_MINER_TARGET_DIFFICULTY=12

# Treasury
TREASURY_AUTO_STAKE_ENABLED=true
TREASURY_TARGET_MULTIPLIER=2.0
```

## 📊 Monitoring

### Logs

```bash
# Bus/Dispatcher logs
docker-compose logs -f ore-bus

# Miner logs
docker-compose logs -f ore-miner-1
```

### Metrics

- **Prometheus**: http://localhost:9091
- **Grafana**: http://localhost:3000 (admin/admin)

### Key Metrics

- Rounds played / won
- Average EV accuracy
- ROI (Return on Investment)
- Current stake multiplier
- Hashrate per worker

## 🔐 OpSec Guide

**CRITICAL SECURITY PRACTICES:**

### 1. Fresh Wallets Only

- **NEVER** reuse existing wallets
- Generate a new wallet specifically for this bot
- Keep wallet keypair encrypted at rest

### 2. Operational Security

- Run on a clean, dedicated server
- Use VPN or bare-metal server (not cloud if possible)
- Isolate network access
- Monitor for unusual activity

### 3. Strategy Secrecy

- **DO NOT** share your strategy parameters
- Keep `ore-strategist` modifications private
- Avoid logging sensitive decision data
- Consider code obfuscation for the strategist module

### 4. Access Control

```bash
# Restrict wallet file permissions
chmod 400 deployment/wallets/bot-wallet.json

# Secure .env file
chmod 600 .env

# Run services as non-root user (Docker does this automatically)
```

### 5. Rate Limiting & Detection Avoidance

- Randomize timing slightly to avoid pattern detection
- Use multiple RPC endpoints
- Monitor for rate limiting
- Consider running your own Solana validator

### 6. Monitoring

- Set up alerts for:
  - Unexpected losses
  - Service downtime
  - Low wallet balance
  - Failed transactions

## 🏦 Treasury Management

The bot automatically manages your ORE rewards:

1. **Auto-Staking**: Reinvests ORE until reaching 2x multiplier
2. **Profit Taking**: Liquidates when ROI threshold is met
3. **Reserve Management**: Maintains minimum SOL for operations

Configure in `.env`:

```bash
TREASURY_AUTO_STAKE_ENABLED=true
TREASURY_TARGET_MULTIPLIER=2.0
TREASURY_PROFIT_TAKE_THRESHOLD=0.50  # 50% ROI
TREASURY_RESERVE_SOL=100000000       # 0.1 SOL
```

## 🎮 Strategy Deep Dive

### Expected Value (EV) Calculation

The bot calculates EV for each of the 25 blocks using:

1. **Base Reward**: Block's share of emission pool (1/25)
2. **Win Probability**: Your stake ÷ total block stake ÷ participant count
3. **Motherlode EV**: Jackpot probability × size
4. **Competition Score**: Stake + participant concentration (0-1)

### Efficiency Gaps

The bot identifies "efficiency gaps": blocks with high EV but low competition.

```
EV/Competition Ratio = Expected Value / (Competition Score + 0.01)
```

### Shadow Board

By monitoring the mempool, the bot builds a "Shadow Board" that predicts:

- Where pending stakes will land
- "Stake traps" (blocks with sudden stake increases)
- "Hidden gems" (undervalued blocks with low pending activity)

### Execution Modes

1. **Normal**: Execute during the round
2. **Sniper**: Wait until last 5 seconds
3. **Aggressive**: Maximum stakes for large motherlodes
4. **Conservative**: Lower risk, smaller stakes

## 📈 Performance Optimization

### GPU Mining

The bot uses CUDA for ~10-20% performance improvement over CPU:

```bash
# Check GPU availability
nvidia-smi

# Configure GPU device
ORE_MINER_GPU_DEVICE_ID=0
```

### Multi-GPU Setup

Run multiple miners:

```bash
# Enable multi-GPU profile
docker-compose --profile multi-gpu up -d
```

### Difficulty Tuning

Higher difficulty = harder to mine but better rewards:

```bash
# Conservative (easier, faster)
ORE_MINER_TARGET_DIFFICULTY=8

# Aggressive (harder, slower, better rewards)
ORE_MINER_TARGET_DIFFICULTY=16
```

## 🧪 Testing

Run tests:

```bash
# All tests
cargo test --workspace

# Specific crate
cargo test -p ore-strategist

# Integration tests
cargo test --test integration
```

## 🐛 Troubleshooting

### Miners not finding solutions

- Lower `ORE_MINER_TARGET_DIFFICULTY`
- Check GPU availability: `nvidia-smi`
- Verify CUDA installation

### Bundle submission failures

- Check Jito tip amount (increase if needed)
- Verify RPC endpoint is not rate limiting
- Check wallet balance

### No strategy decisions

- Verify grid state monitoring is working
- Check WebSocket connection
- Review strategist logs

## 📜 License

MIT License - See LICENSE file

## ⚠️ Disclaimer

This software is provided for educational and research purposes only.

- Use at your own risk
- No guarantees of profitability
- Crypto/DeFi involves significant risk
- Comply with all applicable laws and regulations
- The authors are not responsible for any losses

## 🤝 Contributing

This is a closed-source competitive advantage system.

For security reasons, we do not accept public contributions to the core strategy logic.

## 📞 Support

For critical security issues, contact: [REDACTED]

---

**Built with Rust 🦀 | Powered by Solana ⚡ | Optimized with CUDA 🚀**
