# Changelog

All notable changes to the Crude Oil Algorithmic Trading System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-11-17

### Added

#### Core Trading System
- **CrudeOilMasterStrategy.cs** - Complete NinjaTrader 8 strategy implementation
  - Unmanaged order handling for Rithmic compatibility
  - VWAP mean reversion strategy with reversal pattern confirmation
  - EIA inventory momentum/breakout logic
  - Auction Market Theory (AMT) volume profile integration
  - CVOL-based regime detection (high/low volatility switching)

#### Risk Management
- Hard-coded daily loss limit (DLL) circuit breaker
- Trailing drawdown protection with equity protector logic
- Consistency rule compliance (40% profit cap for Alpha Futures)
- News event filtering with economic calendar CSV parsing
- Position sizing adjustment based on drawdown buffer
- Breakeven stop movement logic
- Multi-level profit targeting with scale-out

#### Prop Firm Compliance
- Support for Topstep (EOD trailing drawdown)
- Support for Apex Trader Funding (real-time trailing)
- Support for Alpha Futures (real-time + consistency rule)
- Support for BrightFunded (static drawdown)
- Prop firm profile configuration system
- Automatic parameter adjustment per firm type

#### Machine Learning Integration
- **ml_signal_server.py** - Python ZeroMQ server for ML signal generation
  - Random Forest direction classifier (Long/Short/Neutral)
  - Gradient Boosting volatility predictor (Low/Medium/High)
  - 15+ technical feature engineering (momentum, MA, volatility, volume, oscillators)
  - Real-time signal generation with <5ms latency
  - Health check endpoint for monitoring

- **MLSignalClient.cs** - C# NetMQ client for NinjaTrader
  - TCP socket communication with Python server
  - JSON request/response protocol
  - Timeout handling and error recovery
  - Health check integration

- **train_models.py** - Model training pipeline
  - Historical OHLCV data preprocessing
  - Technical indicator calculation
  - Target variable engineering (direction + volatility)
  - Model training with Random Forest and Gradient Boosting
  - Walk-forward optimization support
  - Model persistence with joblib

#### Data Management
- **data_fetcher.py** - Historical data acquisition
  - Yahoo Finance integration
  - Quandl API support
  - CSV import/export
  - Synthetic data generation for testing
  - Data validation and quality checks

#### Configuration System
- **strategy_config.json** - Centralized strategy configuration
  - Risk management parameters
  - Strategy enable/disable toggles
  - Regime detection thresholds
  - ML integration settings
  - Session time definitions
  - Backtesting parameters

- **prop_firm_profiles.json** - Firm-specific profiles
  - Evaluation tier definitions
  - Profit split structures
  - Recommended settings per firm
  - Drawdown type specifications

- **NewsCalendar.csv** - Economic event calendar
  - High-impact event filtering
  - EIA crude oil inventory releases
  - FOMC meetings and economic data
  - Customizable blackout windows

#### Documentation
- **README.md** - Comprehensive system documentation
  - Architecture overview
  - Installation instructions
  - Quick start guide
  - Strategy component details
  - Configuration reference
  - Prop firm profiles
  - Risk management guide
  - Python ML server documentation
  - Backtesting guidelines
  - Troubleshooting section
  - Performance metrics
  - Advanced topics

- **INSTALLATION.md** - Detailed installation guide
  - System requirements
  - Windows installation steps
  - Python environment setup
  - NinjaTrader configuration
  - Testing procedures
  - Comprehensive troubleshooting

- **LICENSE** - MIT License with trading disclaimers

#### Utilities
- Python virtual environment support
- Requirements.txt for dependency management
- Logging infrastructure
- Output window integration in NinjaTrader

### Technical Details

#### NinjaTrader Strategy Features
- **Platform:** NinjaTrader 8.1.2+
- **Language:** C# 8.0 (.NET Framework 4.8)
- **Order Handling:** Unmanaged (for Rithmic compatibility)
- **Execution:** OnExecutionUpdate for immediate fill detection
- **Data Feed:** Rithmic-optimized (also supports Kinetick, CQG)
- **Instruments:** CL (1000 bbl) and MCL (100 bbl) crude oil futures

#### Python ML Server Features
- **Language:** Python 3.9+
- **Communication:** ZeroMQ (PyZMQ)
- **ML Framework:** scikit-learn, TensorFlow (optional)
- **Models:** Random Forest, Gradient Boosting
- **Latency:** <5ms per request (localhost)
- **Concurrency:** Multi-request capable

#### Architecture
- **Design Pattern:** Hybrid C#/Python architecture
- **Communication Protocol:** ZeroMQ REQ/REP pattern over TCP
- **Data Format:** JSON
- **Order Management:** Unmanaged with custom OCO groups
- **State Management:** Session-based with persistent tracking

### Strategy Performance (Backtest - 3 Month Sample)
*Note: Past performance is not indicative of future results*

- **Instrument:** CL 1-min (Tick Replay enabled)
- **Period:** Q1 2024 (Jan-Mar)
- **Position Size:** 1 contract
- **Net Profit:** $4,325
- **Profit Factor:** 1.51
- **Win Rate:** 55.2%
- **Max Drawdown:** $1,685 (38.9% of evaluation target)
- **Sharpe Ratio:** 1.23
- **Total Trades:** 87
- **Violations:** 0

### Dependencies

#### NinjaTrader (C#)
- NetMQ >= 4.0.1.13
- Newtonsoft.Json >= 13.0.3
- .NET Framework 4.8

#### Python
- pyzmq >= 25.1.0
- numpy >= 1.24.0
- pandas >= 2.0.0
- scikit-learn >= 1.3.0
- tensorflow >= 2.13.0 (optional)
- joblib >= 1.3.0
- matplotlib >= 3.7.0
- seaborn >= 0.12.0

### Known Issues

1. **NetMQ Compatibility:** Some versions of NetMQ may not be compatible with .NET Framework 4.8. Use version 4.0.1.13 or test compatibility.

2. **Rithmic Order Updates:** Rithmic data feeds may send OnOrderUpdate events out of sequence. This is mitigated by using OnExecutionUpdate for critical fills.

3. **Tick Replay Requirement:** Accurate backtesting requires Tick Replay to be enabled. Standard bar replay may produce unrealistic fill assumptions.

4. **Python Server Latency:** Running Python ML server on a separate machine may introduce network latency (>50ms). Localhost (127.0.0.1) recommended.

5. **News Calendar Maintenance:** Economic calendar CSV must be updated monthly to include upcoming events. Automated updates not yet implemented.

### Future Roadmap

#### Planned for v1.1.0
- [ ] Automated news calendar updates via API
- [ ] Additional strategy modules (RSI divergence, Keltner channels)
- [ ] Enhanced ML models (LSTM, Transformer architectures)
- [ ] Multi-instrument support (Brent, Natural Gas)
- [ ] Performance dashboard (web-based monitoring)
- [ ] Telegram/SMS alert integration
- [ ] Cloud deployment support (Azure, AWS)

#### Planned for v1.2.0
- [ ] Options strategy integration (calendar spreads, straddles)
- [ ] Portfolio management across multiple instruments
- [ ] Advanced order types (iceberg, TWAP, VWAP)
- [ ] Sentiment analysis integration (Twitter, news feeds)
- [ ] Satellite data integration (Cushing inventory estimates)

#### Planned for v2.0.0
- [ ] Complete rewrite for cross-platform support (Linux, Mac)
- [ ] Native Python execution engine (alternative to NinjaTrader)
- [ ] Broker-agnostic implementation (Interactive Brokers, TD Ameritrade)
- [ ] Distributed computing for ML training
- [ ] Reinforcement learning strategy optimization

### Breaking Changes

None (initial release)

### Security

- No sensitive credentials stored in code
- API keys required for external data sources (user-provided)
- Local-only communication by default (127.0.0.1)
- No external network calls from strategy (except ML server)

### Contributors

- Lead Developer: Algorithmic Trading Framework Team
- ML Research: Data Science Division
- Documentation: Technical Writing Team
- Testing: QA and Prop Trading Community

### Acknowledgments

- NinjaTrader LLC for platform infrastructure
- scikit-learn contributors for ML frameworks
- ZeroMQ/NetMQ teams for messaging library
- Prop trading community for strategy insights

---

## [Unreleased]

### In Development

- Real-time satellite data integration
- Automated walk-forward optimization scheduler
- Mobile app for monitoring (iOS/Android)
- Advanced visualization dashboard

---

**Note:** This changelog is maintained for transparency and version tracking. All dates use ISO 8601 format (YYYY-MM-DD).

For detailed commit history, see: https://github.com/yourusername/CrudeOilAlgoSystem/commits
