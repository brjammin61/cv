# 🔮 The Oracle - Prediction Market Alpha Generation System

> **Institutional-grade algorithmic analysis for event derivatives on Kalshi and Polymarket**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=Streamlit&logoColor=white)](https://streamlit.io)

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [System Architecture](#system-architecture)
- [The Five Alpha Engines](#the-five-alpha-engines)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Integration](#api-integration)
- [Risk Management](#risk-management)
- [Disclaimer](#disclaimer)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Overview

**The Oracle** is a sophisticated prediction market analysis system that implements strategies used by the most successful traders in the space, including:

- **Théo ("Trump Whale")**: $50M+ profit using bias correction
- **Domer**: $400M+ volume through structural arbitrage
- **GCR**: Behavioral psychology and liquidity exploitation

The system analyzes markets on **Kalshi** (CFTC-regulated, fiat-based) and **Polymarket** (decentralized, crypto-based) to identify mispricing and generate alpha through quantitative strategies.

### Goal

Turn **$1,000 into $500,000+ within 12 months** by systematically exploiting market inefficiencies with high-conviction, high-accuracy signals.

## ✨ Features

### Core Analytical Engines

1. **Bias Corrector** (Théo Strategy)
   - Corrects for social desirability bias using the "Neighbor Method"
   - Implements the strategy that predicted Trump's 2024 victory with 92% confidence
   - Captures "hidden voters" that traditional polls miss

2. **Favorite-Longshot Adjuster**
   - Exploits systematic mispricing: favorites are underpriced, longshots are overpriced
   - Adds conviction layers to identify high-quality signals
   - Filters out trades that fight known market biases

3. **Risk-Free Rate Adjuster** (Domer Strategy)
   - Treats long-duration contracts as zero-coupon bonds
   - Calculates time-adjusted fair value
   - Identifies opportunities with yields exceeding risk-free rates

4. **Dutch Book Detector**
   - Finds arbitrage in combinatorial markets
   - Detects when sum of probabilities ≠ 100%
   - Locks in risk-free profit

5. **Spatial Arbitrage Detector**
   - Exploits price differences between Kalshi and Polymarket
   - Executes cross-venue arbitrage
   - Captures the "fragmented liquidity premium"

### Dashboard Features

- **Real-time signal generation** across all strategies
- **Multi-tab interface** for deep analysis
- **Customizable filters** (conviction level, minimum edge, strategy selection)
- **Simulated backtesting** mode for risk-free learning
- **Live market data integration** (when API keys configured)
- **Performance tracking** and analytics

## 🚀 Installation

### Prerequisites

- **Python 3.9 or higher**
- **pip** (Python package manager)
- **git** (for cloning repository)

### Step 1: Clone the Repository

```bash
git clone <your-repository-url>
cd oracle_system
```

### Step 2: Run the Setup Script

#### On macOS/Linux:

```bash
chmod +x setup.sh
./setup.sh
```

#### On Windows:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cp config\api_keys.template.py config\api_keys.py
```

### Step 3: Configure API Keys

Edit `config/api_keys.py` with your actual credentials:

```python
# Kalshi credentials
KALSHI_API_KEY = "your_actual_kalshi_api_key"
KALSHI_PRIVATE_KEY_PATH = "/path/to/kalshi_private_key.pem"

# Polymarket credentials
POLYMARKET_PRIVATE_KEY = "0x_your_ethereum_private_key"
POLYGON_RPC_URL = "https://polygon-mainnet.g.alchemy.com/v2/YOUR_API_KEY"
```

⚠️ **SECURITY**: Never commit `api_keys.py` to version control!

## ⚡ Quick Start

### Run in Simulation Mode (No API Keys Required)

```bash
streamlit run oracle_dashboard.py
```

This will launch the dashboard at `http://localhost:8501` using simulated market data.

### Run with Live Data

1. Configure API keys in `config/api_keys.py`
2. Edit `oracle_dashboard.py` and set `simulate_data=False` in the connectors
3. Run the dashboard:

```bash
streamlit run oracle_dashboard.py
```

## 🏗️ System Architecture

```
oracle_system/
│
├── modules/                    # Core analytical engines
│   ├── mod_01_bias_corrector.py
│   ├── mod_02_flb_adjuster.py
│   ├── mod_03_rfr_adjuster.py
│   ├── mod_04_dutchbook_detector.py
│   └── mod_05_spatial_arb_detector.py
│
├── connectors/                 # Exchange API connectors
│   ├── kalshi_connector.py
│   ├── polymarket_connector.py
│   └── data_models.py
│
├── config/                     # Configuration management
│   ├── api_keys.py             (create from template)
│   ├── markets.py              (define your markets here)
│   └── parameters.py           (tune model parameters)
│
├── oracle_dashboard.py         # Main Streamlit dashboard
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 🧠 The Five Alpha Engines

### 1. Bias Corrector (Théo Strategy)

**The Problem**: Traditional polls suffer from social desirability bias - respondents hide controversial preferences.

**The Solution**: The "Neighbor Method" asks "Who will your neighbors vote for?" instead of "Who will you vote for?"

**The Edge**: Captured the "Shy Trump Voter" effect, predicting 2024 results with 92% confidence when polls showed 48%.

```python
from modules import BiasCorrector

corrector = BiasCorrector(shy_voter_weight=0.75)
fair_value = corrector.calculate_fair_value(
    self_pref=0.48,      # Traditional poll: 48%
    neighbor_pref=0.53   # Neighbor poll: 53%
)
# Output: fair_value = 0.515 (51.5%)
# Market at 48 cents = +3.5 cent edge!
```

### 2. Favorite-Longshot Bias

**The Problem**: Markets systematically:
- Underprice heavy favorites (>80% probability)
- Overprice longshots (<20% probability)

**The Solution**: Add a conviction layer that identifies when your signal aligns with this known bias.

**The Edge**: High-conviction signals when buying underpriced favorites or selling overpriced longshots.

### 3. Risk-Free Rate Arbitrage (Domer Strategy)

**The Problem**: Long-duration "sure things" lock up capital but may underperform simple savings accounts.

**The Solution**: Calculate the annualized yield and compare to the risk-free rate.

**The Edge**: Sell overpriced "certainties" that yield less than T-bills, or buy underpriced ones that yield more.

```python
from modules import RiskFreeRateAdjuster

rfr_adjuster = RiskFreeRateAdjuster(risk_free_rate=0.05)  # 5% RFR
signal, rationale = rfr_adjuster.get_time_value_signal(
    market_price=0.98,
    resolution_date=date(2026, 11, 15)
)
# If implied yield < 5%, signal = "SELL" (overpriced)
```

### 4. Dutch Book Detection

**The Problem**: In categorical markets (multiple candidates), retail excitement can push the sum of prices above $1.00.

**The Solution**: Buy or sell all outcomes simultaneously to lock in risk-free profit.

**The Edge**: Risk-free arbitrage when sum ≠ $1.00 (after fees).

### 5. Spatial Arbitrage

**The Problem**: Kalshi and Polymarket have different user bases, leading to price differences for identical events.

**The Solution**: Buy on the cheap venue, sell on the expensive venue.

**The Edge**: Capture the "fragmented liquidity premium" with zero directional risk.

## ⚙️ Configuration

### Adding Markets

Edit `config/markets.py` to add markets you want to trade:

```python
from config.markets import MarketDefinition, MarketCategory, MarketType
from datetime import date

registry.markets.append(MarketDefinition(
    name="2028 Presidential Election",
    category=MarketCategory.POLITICS_US,
    market_type=MarketType.BINARY,
    resolution_date=date(2028, 11, 8),
    kalshi_ticker="PREZ-28",
    polymarket_condition_id="0x1234abcd...",
    enable_bias_correction=True,
    enable_spatial_arb=True,
    enable_rfr_analysis=True
))
```

### Tuning Parameters

Edit `config/parameters.py` to adjust model sensitivity:

```python
# Example: Increase shy voter weight (trust neighbor polls more)
params.bias_corrector.shy_voter_weight = 0.85

# Example: Require higher conviction
params.flb_adjuster.min_edge_cents = 2.0

# Example: Update risk-free rate
params.rfr_adjuster.risk_free_rate = 0.045  # 4.5%
```

## 📊 Usage

### Dashboard Navigation

1. **Live Signals Tab**: View all active trading opportunities
2. **Spatial Arbitrage Tab**: Cross-venue price comparison
3. **Dutch Book Tab**: Combinatorial market analysis
4. **Bias Correction Tab**: Interactive polling bias simulator
5. **Markets Overview Tab**: All configured markets
6. **System Info Tab**: Model parameters and system status

### Filtering Signals

Use the sidebar to filter signals:

- **Minimum Conviction**: NONE, LOW, MEDIUM, HIGH
- **Minimum Edge**: 0.0 to 10.0 cents
- **Strategy Toggles**: Enable/disable specific strategies

### Interpreting Signals

Each signal includes:

- **Strategy**: Which engine generated the signal
- **Market**: The specific prediction market
- **Signal**: BUY, SELL, or specific action
- **Edge**: Potential profit in cents
- **Conviction**: Quality rating (NONE to HIGH)
- **Details**: Full rationale and calculations

## 🔌 API Integration

### Kalshi API Setup

1. Create account at [kalshi.com](https://kalshi.com)
2. Generate API key in account settings
3. Download RSA private key
4. Add credentials to `config/api_keys.py`

Documentation: [Kalshi API Docs](https://docs.kalshi.com/)

### Polymarket API Setup

1. Create Ethereum wallet (MetaMask, etc.)
2. Fund with USDC on Polygon network
3. Export private key
4. Get Polygon RPC endpoint (Alchemy, Infura, QuickNode)
5. Add credentials to `config/api_keys.py`

Documentation: [Polymarket CLOB API](https://docs.polymarket.com/)

## ⚠️ Risk Management

### Built-in Safety Features

- **Kelly Criterion Position Sizing** (default: 0.25 fractional Kelly)
- **Maximum Position Size** (default: 10% of capital)
- **Maximum Total Exposure** (default: 50% of capital)
- **Emergency Kill Switch** (set `EMERGENCY_STOP = True` in config)

### Best Practices

1. **Start Small**: Test with minimum capital ($100-$500)
2. **Use Simulation Mode**: Practice without real money first
3. **Verify Signals Manually**: Always double-check before placing trades
4. **Track Performance**: Log all trades and analyze results
5. **Never Bet More Than You Can Afford to Lose**

### Risk Disclosure

⚠️ **WARNING**: Trading prediction markets involves substantial risk of loss. This system:

- **Does NOT guarantee profits**
- **Past performance does NOT predict future results**
- **May experience significant drawdowns**
- **Requires active monitoring**
- **Is for educational purposes only**

You are solely responsible for your trading decisions and outcomes.

## 🛠️ Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black modules/ connectors/ config/
flake8 modules/ connectors/ config/
```

### Type Checking

```bash
mypy modules/ connectors/ config/
```

## 📝 Disclaimer

**THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.**

This system is for **educational and informational purposes only**. The creators:

- Are NOT registered investment advisors
- Do NOT guarantee any specific results
- Are NOT liable for any losses incurred
- Do NOT provide financial advice

**You use this software entirely at your own risk.**

Always:
- Do your own research
- Consult with financial professionals
- Never risk more than you can afford to lose
- Comply with all applicable laws and regulations

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

This system implements strategies inspired by:

- **Théo** - Bias correction methodology
- **Domer** - Structural arbitrage and time-value analysis
- **GCR** - Behavioral psychology and market dynamics
- The broader prediction market research community

## 📞 Support

For issues, questions, or suggestions:

- **GitHub Issues**: [Open an issue](https://github.com/yourusername/oracle/issues)
- **Documentation**: [Wiki](https://github.com/yourusername/oracle/wiki)

## 🎯 Roadmap

### Version 1.0 (Current)
- ✅ Five core analytical engines
- ✅ Streamlit dashboard
- ✅ Simulation mode
- ✅ Kalshi & Polymarket connectors

### Version 1.1 (Planned)
- [ ] Automated backtesting engine
- [ ] Advanced polling data ingestion
- [ ] ML-based signal enhancement
- [ ] Telegram/Discord alerts
- [ ] Portfolio optimization

### Version 2.0 (Future)
- [ ] Automated trade execution (optional)
- [ ] Multi-user support
- [ ] Cloud deployment
- [ ] Mobile app

---

**Built with ❤️ for prediction market traders**

*Remember: The best trades are the ones you understand. Study the strategies, validate the signals, and trade responsibly.*
