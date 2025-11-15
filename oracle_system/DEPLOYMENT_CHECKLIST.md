# 🚀 Oracle Deployment Checklist

Use this checklist to deploy The Oracle system safely and successfully.

## Phase 1: Installation & Setup ✅

- [ ] **Clone/Download Project**
  ```bash
  cd /path/to/oracle_system
  ```

- [ ] **Run Setup Script**
  ```bash
  chmod +x setup.sh
  ./setup.sh
  ```

- [ ] **Activate Virtual Environment**
  ```bash
  source venv/bin/activate  # macOS/Linux
  # OR
  venv\Scripts\activate  # Windows
  ```

- [ ] **Test Installation**
  ```bash
  python test_installation.py
  ```
  - All tests should pass ✅

## Phase 2: Configuration 📝

- [ ] **Configure API Keys** (Skip for simulation mode)
  - Copy template: `cp config/api_keys.template.py config/api_keys.py`
  - Edit `config/api_keys.py` with real credentials
  - **Kalshi**: API key + private key path
  - **Polymarket**: Ethereum private key + Polygon RPC URL
  - Validate: `python -c "from config.api_keys import validate_credentials; validate_credentials()"`

- [ ] **Add Your Markets**
  - Edit `config/markets.py`
  - Add markets to `_load_default_markets()` method
  - Include Kalshi tickers and Polymarket condition IDs
  - Enable appropriate strategies for each market

- [ ] **Tune Parameters** (Optional)
  - Edit `config/parameters.py`
  - Adjust `shy_voter_weight`, `risk_free_rate`, etc.
  - Save custom configuration: `params.save_to_file('my_params.json')`

## Phase 3: Testing (Simulation Mode) 🧪

- [ ] **Launch Dashboard**
  ```bash
  streamlit run oracle_dashboard.py
  ```
  - Should open browser to `http://localhost:8501`

- [ ] **Verify All Tabs Load**
  - [ ] Live Signals
  - [ ] Spatial Arbitrage
  - [ ] Dutch Book
  - [ ] Bias Correction
  - [ ] Markets Overview
  - [ ] System Info

- [ ] **Test Each Strategy**
  - [ ] BiasCorrector: Try the interactive sliders
  - [ ] FLB: Check conviction levels
  - [ ] RFR: Verify time-value calculations
  - [ ] DutchBook: See arbitrage detection
  - [ ] SpatialArb: Compare venue prices

- [ ] **Verify Signal Generation**
  - Signals should appear in "Live Signals" tab
  - Check signal details are complete
  - Verify edge calculations make sense

## Phase 4: Paper Trading 📊

- [ ] **Enable Live Data** (Keep trades manual)
  - Edit `oracle_dashboard.py`
  - Set `simulate_data=False` in connectors
  - Restart dashboard

- [ ] **Create Trading Journal**
  - Spreadsheet or notebook
  - Track: Date, Market, Strategy, Signal, Edge, Outcome

- [ ] **Track Signals for 1-2 Weeks**
  - Log every HIGH conviction signal
  - Verify prices manually on exchanges
  - Calculate hypothetical P&L

- [ ] **Analyze Results**
  - Calculate win rate
  - Average edge captured
  - Sharpe ratio
  - ROI

## Phase 5: Small Capital Live Trading 💰

**ONLY proceed if paper trading was successful (>65% win rate, >2.5¢ avg edge)**

- [ ] **Fund Accounts**
  - Kalshi: Deposit $100-500
  - Polymarket: Bridge USDC to Polygon ($100-500)

- [ ] **Set Strict Rules**
  - [ ] ONLY trade HIGH conviction signals
  - [ ] Maximum position size: $50 (10% of $500)
  - [ ] Maximum daily risk: $100 (20% of $500)
  - [ ] Stop trading after 2 losses in a row

- [ ] **Execute First Trade**
  - Wait for HIGH conviction signal with >4¢ edge
  - Verify prices manually on exchange
  - Start with smallest position size
  - Log everything

- [ ] **Track Performance Daily**
  - Update trading journal
  - Calculate running P&L
  - Monitor win rate and average edge

## Phase 6: Scaling Up 📈

**ONLY scale after 1 month of profitable live trading**

- [ ] **Performance Validation**
  - [ ] Win rate > 65%
  - [ ] Average edge > 2.5¢
  - [ ] Positive ROI for the month
  - [ ] At least 10 trades executed

- [ ] **Increase Capital Gradually**
  - Week 1-4: $500
  - Week 5-8: $1,000
  - Week 9-12: $2,500
  - Month 4+: $5,000+

- [ ] **Optimize Strategy**
  - Review losing trades
  - Identify best-performing strategies
  - Tune parameters based on results
  - Add more markets

## Phase 7: Advanced Features (Optional) 🔧

- [ ] **Automated Data Collection**
  - Set up cron jobs for polling data scraping
  - Store historical data in `data/` directory
  - Build backtesting datasets

- [ ] **Performance Monitoring**
  - Set up alerts (Telegram/Discord bot)
  - Track signals automatically
  - Generate weekly reports

- [ ] **Custom Strategies**
  - Add new analytical modules
  - Implement machine learning enhancements
  - Build custom indicators

## Safety Checklist ⚠️

Before going live, verify:

- [ ] **Never commit API keys to git**
  - Check: `git status` should NOT show `api_keys.py`
  - Verify: `.gitignore` includes `api_keys.py`

- [ ] **Risk limits are set**
  - `MAX_POSITION_SIZE_PERCENT` configured
  - `MAX_TOTAL_EXPOSURE_PERCENT` configured
  - Emergency stop enabled if needed

- [ ] **Understand every strategy**
  - Can explain BiasCorrector in your own words
  - Know when FLB adds conviction
  - Understand RFR time-value concept
  - Can identify Dutch Book opportunities
  - Recognize spatial arb signals

- [ ] **Have exit plan**
  - Know how to close positions
  - Understand withdrawal process
  - Can stop trading immediately if needed

## Troubleshooting 🔧

### Dashboard Won't Start

```bash
# Check Python version
python --version  # Need 3.9+

# Reinstall dependencies
pip install -r requirements.txt --upgrade

# Check for errors
python oracle_dashboard.py --help
```

### No Signals Appearing

- Lower minimum edge threshold (sidebar)
- Change conviction filter to "LOW"
- Enable all strategy toggles
- Check if markets are configured correctly

### API Connection Errors

- Verify credentials in `config/api_keys.py`
- Check network connectivity
- Confirm API keys have correct permissions
- Review logs in `logs/oracle_dashboard.log`

### Incorrect Edge Calculations

- Verify market prices are current
- Check fee parameters match actual exchange fees
- Review strategy logic in module source code
- Test with known examples

## Success Metrics 📊

Track these weekly:

| Metric | Target | Current |
|--------|--------|---------|
| Signals Generated | 10-20 | ___ |
| High Conviction % | >30% | ___ |
| Win Rate | >65% | ___ |
| Average Edge | >2.5¢ | ___ |
| ROI (Monthly) | >30% | ___ |
| Sharpe Ratio | >1.5 | ___ |

## Final Pre-Launch Checklist ✈️

Before risking real money:

- [ ] ✅ All installation tests pass
- [ ] ✅ Paper trading results are positive
- [ ] ✅ Win rate validated over 10+ trades
- [ ] ✅ Risk management rules defined
- [ ] ✅ Trading journal ready
- [ ] ✅ Fully understand all strategies
- [ ] ✅ Can explain signals to someone else
- [ ] ✅ Comfortable with potential losses
- [ ] ✅ Have realistic expectations
- [ ] ✅ Ready to learn and adapt

## Emergency Procedures 🚨

If something goes wrong:

1. **Stop trading immediately**
   - Set `EMERGENCY_STOP = True` in `config/api_keys.py`
   - Close all open positions
   - Withdraw funds if necessary

2. **Preserve evidence**
   - Save all logs from `logs/` directory
   - Export trading journal
   - Screenshot error messages

3. **Analyze what happened**
   - Review recent trades
   - Check system logs
   - Identify root cause

4. **Get help**
   - Check documentation
   - Review error messages
   - Search for similar issues

5. **Fix and restart**
   - Address root cause
   - Test fix in simulation mode
   - Resume cautiously with small positions

---

**Remember**: The goal is consistent, compounding returns. Not get-rich-quick.

Take your time. Follow the checklist. Trade smart. 🎯
