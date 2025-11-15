# 🚀 Quick Start Guide - The Oracle

Get up and running with The Oracle in **under 5 minutes**.

## Step 1: Install (2 minutes)

```bash
cd oracle_system
chmod +x setup.sh
./setup.sh
```

This will:
- Create a Python virtual environment
- Install all dependencies
- Create configuration template

## Step 2: Launch Dashboard (30 seconds)

```bash
source venv/bin/activate  # Activate virtual environment
streamlit run oracle_dashboard.py
```

Your browser will automatically open to `http://localhost:8501`

## Step 3: Explore (2 minutes)

### Try the Bias Corrector

1. Click the **"Bias Correction"** tab
2. Adjust the polling sliders:
   - Self Preference: 48%
   - Neighbor Preference: 53%
3. Watch the model calculate the "true" fair value
4. See the edge vs current market price

### Check Live Signals

1. Go to the **"Live Signals"** tab
2. See all active trading opportunities
3. Click **"Top Signal Details"** to see full analysis
4. Adjust filters in the sidebar to customize

### View Spatial Arbitrage

1. Open the **"Spatial Arbitrage"** tab
2. See price differences between Kalshi and Polymarket
3. Identify cross-venue opportunities

## Step 4: Customize (Optional)

### Add Your Markets

Edit `config/markets.py`:

```python
from config.markets import MarketDefinition, MarketCategory, MarketType
from datetime import date

# Add to the _load_default_markets() method:
self.markets.append(MarketDefinition(
    name="Your Market Name",
    category=MarketCategory.POLITICS_US,
    market_type=MarketType.BINARY,
    resolution_date=date(2026, 11, 3),
    # Add your Kalshi ticker
    kalshi_ticker="YOUR-TICKER",
    # Add your Polymarket condition ID
    polymarket_condition_id="0xYOUR_ID",
    enable_spatial_arb=True
))
```

### Tune Parameters

Edit `config/parameters.py`:

```python
# Make the model more aggressive
params.bias_corrector.shy_voter_weight = 0.85  # Trust neighbor polls more
params.flb_adjuster.min_edge_cents = 1.0  # Lower edge threshold
params.rfr_adjuster.risk_free_rate = 0.045  # Update to current rates
```

## Step 5: Go Live (When Ready)

### Get API Credentials

**Kalshi:**
1. Sign up at [kalshi.com](https://kalshi.com)
2. Go to Settings → API
3. Generate API key and download private key

**Polymarket:**
1. Create Ethereum wallet (MetaMask)
2. Get private key
3. Get Polygon RPC URL from [Alchemy](https://www.alchemy.com/)

### Configure Credentials

Edit `config/api_keys.py`:

```python
# Kalshi
KALSHI_API_KEY = "your_actual_api_key"
KALSHI_PRIVATE_KEY_PATH = "/path/to/your/key.pem"

# Polymarket
POLYMARKET_PRIVATE_KEY = "0x_your_private_key"
POLYGON_RPC_URL = "https://polygon-mainnet.g.alchemy.com/v2/YOUR_KEY"
```

### Switch to Live Mode

Edit `oracle_dashboard.py` (around line 75):

```python
# Change this:
st.session_state.kalshi = KalshiConnector(simulate_data=True)
st.session_state.polymarket = PolymarketConnector(simulate_data=True)

# To this:
st.session_state.kalshi = KalshiConnector(
    api_key=KALSHI_API_KEY,
    private_key_path=KALSHI_PRIVATE_KEY_PATH,
    simulate_data=False
)
st.session_state.polymarket = PolymarketConnector(
    private_key=POLYMARKET_PRIVATE_KEY,
    polygon_rpc=POLYGON_RPC_URL,
    simulate_data=False
)
```

## 📊 Understanding Signals

### Signal Types

- **BUY**: Market is underpricing this outcome
- **SELL**: Market is overpricing this outcome
- **BUY_KALSHI_SELL_POLY**: Buy on Kalshi, sell on Polymarket
- **BUY_POLY_SELL_KALSHI**: Buy on Polymarket, sell on Kalshi
- **BUY_ALL**: Buy all outcomes (Dutch Book under-round)
- **SELL_ALL**: Sell all outcomes (Dutch Book over-round)

### Conviction Levels

- **HIGH**: Model strongly supports this trade (bias aligns with signal)
- **MEDIUM**: Standard signal (neutral bias)
- **LOW**: Weak signal (model fights known biases)
- **NONE**: No edge detected

### Edge Calculation

**Edge** = Fair Value - Market Price (in cents)

- Edge > 2.0¢: Strong opportunity
- Edge > 5.0¢: Exceptional opportunity
- Edge < 1.0¢: Marginal opportunity

## ⚠️ Safety Tips

1. **Start with Simulation**: Practice for at least a week
2. **Paper Trade**: Log signals and track hypothetical performance
3. **Start Small**: Begin with $100-$500
4. **Verify Manually**: Always check prices on the exchange before trading
5. **Set Limits**: Never risk more than 10% on a single trade
6. **Track Performance**: Log every trade and analyze results weekly

## 🆘 Troubleshooting

### Dashboard won't start

```bash
# Check Python version (need 3.9+)
python --version

# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

### No signals showing

- Check your filter settings (sidebar)
- Lower minimum edge threshold
- Enable all strategy toggles

### API errors

- Verify credentials in `config/api_keys.py`
- Check API key permissions
- Ensure wallets are funded (Polymarket)

## 📚 Learn More

- **Full Documentation**: See [README.md](README.md)
- **Model Details**: Check individual module files in `modules/`
- **Configuration**: Review `config/parameters.py`

## 🎯 Next Steps

1. **Week 1**: Study the strategies, understand each module
2. **Week 2**: Paper trade and track results
3. **Week 3**: Backtest on historical markets
4. **Week 4**: Start live trading with minimum capital
5. **Week 5+**: Scale up as you gain confidence

---

**Ready to find alpha? Let's go! 🚀**

*Questions? Check the [README.md](README.md) or open an issue on GitHub.*
