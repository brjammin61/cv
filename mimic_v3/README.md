# MIMIC V3.1 - Kalshi Native Trading System

High-frequency trading system for Kalshi prediction markets with whale detection, AI sentiment analysis, and adaptive risk management.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     MIMIC CORTEX                            │
├─────────────┬─────────────┬─────────────┬──────────────────┤
│   Scanner   │    Brain    │   Oracle    │   Risk Engine    │
│  (Whales)   │  (ML/River) │ (Sentiment) │ (Kelly + DDC)    │
├─────────────┴─────────────┴─────────────┴──────────────────┤
│                    Market Maker (LIP)                       │
├─────────────────────────────────────────────────────────────┤
│                   Kalshi Client (REST + WS)                 │
└─────────────────────────────────────────────────────────────┘
```

## Components

### Scanner (`scanner.py`)
- Shadow ID tracking for whale fingerprinting
- Volume spike detection
- Resolution arbitrage detection
- Order flow imbalance analysis

### Brain (`brain.py`)
- River online learning (real-time model updates)
- Feature engineering from market signals
- Target encoding for shadow IDs
- Probability calibration

### Oracle (`news_oracle.py`)
- Perplexity API integration for news sentiment
- Context-aware market analysis
- Response caching and rate limiting

### Risk Engine (`risk_engine.py`)
- **Asymptotic Kelly Criterion** (accounts for estimation error)
- Dynamic Drawdown Control (DDC)
- Daily/weekly loss limits
- Per-market and event exposure caps

### Market Maker (`maker.py`)
- LIP rebate farming
- Favorite-Longshot Bias exploitation
- Inventory risk management

## Quick Start

### 1. Clone and Deploy

```bash
# On your DigitalOcean droplet
git clone <your-repo-url>
cd mimic_v3
sudo ./deploy.sh
```

### 2. Configure API Keys

```bash
nano .env
```

Add your credentials:
```
KALSHI_API_KEY=your_key
KALSHI_API_SECRET=your_secret
PERPLEXITY_API_KEY=your_pplx_key
```

### 3. Test (Paper Trading)

```bash
source venv/bin/activate
python main_mimic.py --demo
```

### 4. Start Service

```bash
sudo systemctl start mimic
sudo systemctl status mimic
```

### 5. Monitor

```bash
# System logs
journalctl -u mimic -f

# Application logs
tail -f logs/mimic_cortex.log
```

## Command Line Options

```bash
python main_mimic.py [OPTIONS]

Options:
  --demo      Use Kalshi demo API endpoints
  --live      Enable live trading (disables paper mode)
  --capital   Initial capital amount (default: 1000.0)
```

## Risk Management

The system uses Asymptotic Kelly for position sizing:

```
f* = (p - q/b) / (1 + 1/n)
```

Where:
- `p` = win probability
- `q` = 1 - p
- `b` = payout ratio
- `n` = estimation samples

Additional safeguards:
- Daily loss limit: $50
- Weekly loss limit: $150
- Max position: 10% of capital
- 30% drawdown halt

## Trading Flow

1. **Scanner** detects whale activity
2. **Fast Lane** (Arbitrage): Skip Oracle, direct to Brain
3. **Slow Lane** (Informational): Oracle validates with news
4. **Brain** predicts win probability
5. **Risk Engine** calculates position size
6. **Execute** or reject based on risk limits

## Files

```
mimic_v3/
├── main_mimic.py           # Central orchestrator
├── deploy.sh               # Deployment script
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
├── config/
│   └── mimic.service      # systemd service file
├── modules/
│   └── mimic_v3/
│       ├── kalshi_client.py   # API client
│       ├── scanner.py         # Whale detection
│       ├── brain.py           # ML prediction
│       ├── risk_engine.py     # Risk management
│       ├── news_oracle.py     # Sentiment analysis
│       ├── maker.py           # Market making
│       └── context_parser.py  # Kalshi parsing
├── logs/                   # Log files
└── models/                 # Saved ML models
```

## Safety Notes

1. **Always start with paper trading**
2. **Use demo mode first** to verify connectivity
3. **Set conservative risk limits** initially
4. **Monitor closely** during first live sessions
5. **Never deploy with API keys in code**

## License

Proprietary - All Rights Reserved
