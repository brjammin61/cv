"""
THE ORACLE - Main Dashboard

Real-time prediction market analysis dashboard powered by Streamlit.

This is the main entry point for the Oracle system. It integrates all
analytical modules and presents actionable trading signals.

Usage:
    streamlit run oracle_dashboard.py
"""

import streamlit as st
import pandas as pd
import time
from datetime import datetime, date, timedelta
import logging
from typing import Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/oracle_dashboard.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import Oracle modules
from modules import (
    BiasCorrector,
    FavoriteLongshotAdjuster,
    RiskFreeRateAdjuster,
    DutchBookDetector,
    SpatialArbitrageDetector
)

from config.parameters import OracleParameters
from config.markets import MarketRegistry, MarketCategory

from connectors import KalshiConnector, PolymarketConnector

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="The Oracle - Prediction Market Alpha",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if 'initialized' not in st.session_state:
    logger.info("Initializing Oracle dashboard...")

    # Load parameters and market registry
    st.session_state.params = OracleParameters()
    st.session_state.registry = MarketRegistry()

    # Initialize analytical modules
    st.session_state.engines = {
        'bias_corrector': BiasCorrector(
            shy_voter_weight=st.session_state.params.bias_corrector.shy_voter_weight
        ),
        'flb_adjuster': FavoriteLongshotAdjuster(
            favorite_threshold=st.session_state.params.flb_adjuster.favorite_threshold,
            longshot_threshold=st.session_state.params.flb_adjuster.longshot_threshold
        ),
        'rfr_adjuster': RiskFreeRateAdjuster(
            risk_free_rate=st.session_state.params.rfr_adjuster.risk_free_rate
        ),
        'dutchbook_detector': DutchBookDetector(
            transaction_fee_per_share=st.session_state.params.dutchbook.transaction_fee_per_share
        ),
        'spatial_arb_detector': SpatialArbitrageDetector(
            total_fee_cost=st.session_state.params.spatial_arb.total_fee_cost
        )
    }

    # Initialize connectors (using simulation mode by default)
    st.session_state.kalshi = KalshiConnector(simulate_data=True)
    st.session_state.polymarket = PolymarketConnector(simulate_data=True)

    # Market data storage
    st.session_state.market_data = {}
    st.session_state.signals = []
    st.session_state.last_update = datetime.now()

    st.session_state.initialized = True
    logger.info("✅ Oracle dashboard initialized successfully")

# ============================================================================
# SIDEBAR - CONTROLS & CONFIGURATION
# ============================================================================

with st.sidebar:
    st.title("🔮 The Oracle")
    st.markdown("### Prediction Market Alpha Generation")

    st.divider()

    # Status indicators
    st.markdown("#### System Status")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Kalshi", "🟢 Connected" if st.session_state.kalshi.connected else "🔴 Offline")
    with col2:
        st.metric("Polymarket", "🟢 Connected" if st.session_state.polymarket.connected else "🔴 Offline")

    # Last update time
    time_since_update = (datetime.now() - st.session_state.last_update).seconds
    st.metric("Last Update", f"{time_since_update}s ago")

    st.divider()

    # Signal filters
    st.markdown("#### Signal Filters")

    min_conviction = st.selectbox(
        "Minimum Conviction",
        ["NONE", "LOW", "MEDIUM", "HIGH"],
        index=2  # Default to MEDIUM
    )

    min_edge = st.slider(
        "Minimum Edge (cents)",
        min_value=0.0,
        max_value=10.0,
        value=1.0,
        step=0.5
    )

    show_spatial_arb = st.checkbox("Spatial Arbitrage", value=True)
    show_dutch_book = st.checkbox("Dutch Book", value=True)
    show_bias_correction = st.checkbox("Bias Correction", value=True)
    show_rfr = st.checkbox("RFR Analysis", value=True)

    st.divider()

    # Parameters
    with st.expander("⚙️ Model Parameters"):
        st.markdown("**Bias Corrector**")
        shy_voter_weight = st.slider(
            "Shy Voter Weight",
            0.0, 1.0,
            st.session_state.params.bias_corrector.shy_voter_weight,
            0.05
        )

        st.markdown("**Risk-Free Rate**")
        rfr = st.slider(
            "Annual RFR (%)",
            0.0, 10.0,
            st.session_state.params.rfr_adjuster.risk_free_rate * 100,
            0.25
        ) / 100

    # Refresh button
    if st.button("🔄 Refresh Data", type="primary", use_container_width=True):
        st.rerun()

    st.divider()

    # Mode indicator
    st.warning("⚠️ **SIMULATION MODE**\n\nUsing simulated market data. Configure API keys in `config/api_keys.py` for live data.")

# ============================================================================
# MAIN DASHBOARD
# ============================================================================

st.title("🔮 The Oracle - Prediction Market Analysis")
st.markdown("*Institutional-grade alpha generation for event derivatives*")

# Display disclaimer
st.info(
    "**⚠️ DISCLAIMER**: This system is for informational and educational purposes only. "
    "Trading prediction markets involves substantial risk. Past performance does not guarantee future results. "
    "Always do your own research and never risk more than you can afford to lose."
)

st.divider()

# ============================================================================
# TAB LAYOUT
# ============================================================================

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Live Signals",
    "🛰️ Spatial Arbitrage",
    "💰 Dutch Book",
    "🧠 Bias Correction",
    "📈 Markets Overview",
    "⚙️ System Info"
])

# ============================================================================
# TAB 1: LIVE SIGNALS (Main Dashboard)
# ============================================================================

with tab1:
    st.header("Live Trading Signals")

    # Generate signals
    signals = []

    # Example: Spatial Arbitrage Signals
    if show_spatial_arb:
        spatial_markets = st.session_state.registry.get_spatial_arb_markets()

        for market in spatial_markets[:3]:  # Limit to 3 for demo
            # Simulate fetching data
            kalshi_book = st.session_state.kalshi.get_order_book(
                market.kalshi_ticker or "DEMO-TICKER",
                market.name
            )
            poly_book = st.session_state.polymarket.get_order_book(
                market.polymarket_condition_id or "0x1234...",
                market.name
            )

            if kalshi_book and poly_book:
                signal, rationale = st.session_state.engines['spatial_arb_detector'].find_arbitrage(
                    kalshi_book.best_bid,
                    kalshi_book.best_ask,
                    poly_book.best_bid,
                    poly_book.best_ask,
                    market.name
                )

                if signal != "HOLD":
                    edge = 0
                    if signal == "BUY_KALSHI_SELL_POLY":
                        edge = (poly_book.best_bid - kalshi_book.best_ask) * 100
                    elif signal == "BUY_POLY_SELL_KALSHI":
                        edge = (kalshi_book.best_bid - poly_book.best_ask) * 100

                    if edge >= min_edge:
                        signals.append({
                            'Strategy': 'Spatial Arb',
                            'Market': market.name,
                            'Signal': signal.replace('_', ' ').title(),
                            'Edge (¢)': f"{edge:.2f}",
                            'Conviction': 'HIGH',
                            'Details': rationale
                        })

    # Display signals
    if signals:
        df_signals = pd.DataFrame(signals)

        # Style the dataframe
        st.dataframe(
            df_signals,
            use_container_width=True,
            hide_index=True
        )

        st.success(f"✅ **{len(signals)} active signal(s) detected**")

        # Show top signal details
        if len(signals) > 0:
            with st.expander("📋 Top Signal Details"):
                top_signal = signals[0]
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Strategy", top_signal['Strategy'])
                    st.metric("Market", top_signal['Market'])

                with col2:
                    st.metric("Signal", top_signal['Signal'])
                    st.metric("Conviction", top_signal['Conviction'])

                with col3:
                    st.metric("Edge", top_signal['Edge (¢)'])

                st.markdown("**Full Analysis:**")
                st.info(top_signal['Details'])
    else:
        st.warning("No signals match current filters. Try adjusting your filter settings.")

    # Performance metrics (simulated)
    st.divider()
    st.subheader("📈 Hypothetical Performance")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Signals (24h)", "47", "+12")
    with col2:
        st.metric("Avg Edge", "3.2¢", "+0.8¢")
    with col3:
        st.metric("Win Rate", "68%", "+5%")
    with col4:
        st.metric("Sharpe Ratio", "2.4", "+0.3")

# ============================================================================
# TAB 2: SPATIAL ARBITRAGE
# ============================================================================

with tab2:
    st.header("🛰️ Spatial Arbitrage (Cross-Venue)")

    st.markdown("""
    This module exploits price differences between Kalshi (regulated, fiat) and
    Polymarket (crypto, global) for the same event.
    """)

    # Example markets
    spatial_markets = st.session_state.registry.get_spatial_arb_markets()

    if spatial_markets:
        for market in spatial_markets[:5]:
            with st.container():
                st.subheader(market.name)

                # Simulate order book data
                kalshi_book = st.session_state.kalshi.get_order_book(
                    market.kalshi_ticker or "DEMO",
                    market.name
                )
                poly_book = st.session_state.polymarket.get_order_book(
                    market.polymarket_condition_id or "0x...",
                    market.name
                )

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown("**Kalshi**")
                    if kalshi_book:
                        st.metric("Bid", f"{kalshi_book.best_bid:.3f}")
                        st.metric("Ask", f"{kalshi_book.best_ask:.3f}")
                        st.metric("Mid", f"{kalshi_book.mid_price:.3f}")

                with col2:
                    st.markdown("**Polymarket**")
                    if poly_book:
                        st.metric("Bid", f"{poly_book.best_bid:.3f}")
                        st.metric("Ask", f"{poly_book.best_ask:.3f}")
                        st.metric("Mid", f"{poly_book.mid_price:.3f}")

                with col3:
                    st.markdown("**Analysis**")
                    if kalshi_book and poly_book:
                        signal, rationale = st.session_state.engines['spatial_arb_detector'].find_arbitrage(
                            kalshi_book.best_bid,
                            kalshi_book.best_ask,
                            poly_book.best_bid,
                            poly_book.best_ask
                        )

                        if signal == "HOLD":
                            st.info("No arbitrage opportunity")
                        else:
                            st.success(f"**{signal.replace('_', ' ').title()}**")
                            st.caption(rationale)

                st.divider()
    else:
        st.warning("No spatial arbitrage markets configured. Add markets in `config/markets.py`")

# ============================================================================
# TAB 3: DUTCH BOOK
# ============================================================================

with tab3:
    st.header("💰 Dutch Book Arbitrage")

    st.markdown("""
    This module detects when the sum of probabilities in a categorical market
    deviates from 100%, creating risk-free arbitrage opportunities.
    """)

    # Example categorical market
    dutch_markets = st.session_state.registry.get_dutch_book_markets()

    if dutch_markets:
        for market in dutch_markets:
            st.subheader(market.name)

            # Simulate outcome prices
            outcome_prices = {
                "Trump": 0.45,
                "DeSantis": 0.32,
                "Haley": 0.18,
                "Other": 0.08
            }

            # Display outcomes
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown("**Outcome Prices:**")
                for outcome, price in outcome_prices.items():
                    st.metric(outcome, f"{price:.2f}", f"{price*100:.1f}%")

            with col2:
                st.markdown("**Analysis:**")
                price_sum = sum(outcome_prices.values())
                st.metric("Sum of Prices", f"{price_sum:.4f}")

                signal, rationale = st.session_state.engines['dutchbook_detector'].find_arbitrage(
                    outcome_prices,
                    market.name
                )

                if signal == "HOLD":
                    st.success("✅ Market is efficient")
                else:
                    st.warning(f"⚠️ **{signal}**")
                    st.caption(rationale)

            st.divider()
    else:
        st.warning("No Dutch Book markets configured. Add markets in `config/markets.py`")

# ============================================================================
# TAB 4: BIAS CORRECTION
# ============================================================================

with tab4:
    st.header("🧠 Bias Correction (Théo Strategy)")

    st.markdown("""
    This module corrects for social desirability bias in polling data using the
    "Neighbor Method" - the strategy that made $50M+ in 2024.
    """)

    # Example: Simulate polling data
    st.subheader("Example: 2028 Presidential Race")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Raw Polling Data:**")
        self_pref = st.slider("Self Preference ('Who will YOU vote for?')", 0.0, 1.0, 0.48, 0.01)
        neighbor_pref = st.slider("Neighbor Preference ('Who will NEIGHBORS vote for?')", 0.0, 1.0, 0.53, 0.01)

    with col2:
        st.markdown("**Bias-Corrected Analysis:**")

        fair_value = st.session_state.engines['bias_corrector'].calculate_fair_value(
            self_pref,
            neighbor_pref,
            "Example Market"
        )

        st.metric("Model Fair Value", f"{fair_value:.1%}")
        st.metric("Shy Voter Index", f"{neighbor_pref - self_pref:.1%}")

        # Compare to market price
        market_price = st.slider("Current Market Price", 0.0, 1.0, 0.48, 0.01)
        edge = (fair_value - market_price) * 100

        st.metric("Edge vs Market", f"{edge:+.2f}¢")

        if edge > 1.0:
            st.success(f"✅ **BUY SIGNAL** - Market underpricing by {edge:.2f}¢")
        elif edge < -1.0:
            st.error(f"⚠️ **SELL SIGNAL** - Market overpricing by {abs(edge):.2f}¢")
        else:
            st.info("⏸️ **HOLD** - Market is fairly priced")

# ============================================================================
# TAB 5: MARKETS OVERVIEW
# ============================================================================

with tab5:
    st.header("📈 Markets Overview")

    # Market registry summary
    all_markets = st.session_state.registry.get_all_markets()

    st.metric("Total Active Markets", len(all_markets))

    # Group by category
    st.subheader("Markets by Category")

    for category in MarketCategory:
        markets_in_category = st.session_state.registry.get_markets_by_category(category)

        if markets_in_category:
            with st.expander(f"{category.value.replace('_', ' ').title()} ({len(markets_in_category)})"):
                for market in markets_in_category:
                    st.markdown(f"**{market.name}**")
                    st.caption(f"Type: {market.market_type.value} | Resolution: {market.resolution_date or 'TBD'}")

                    strategies = []
                    if market.enable_spatial_arb:
                        strategies.append("Spatial Arb")
                    if market.enable_dutch_book:
                        strategies.append("Dutch Book")
                    if market.enable_bias_correction:
                        strategies.append("Bias Correction")
                    if market.enable_rfr_analysis:
                        strategies.append("RFR")

                    st.caption(f"Strategies: {', '.join(strategies)}")
                    st.divider()

# ============================================================================
# TAB 6: SYSTEM INFO
# ============================================================================

with tab6:
    st.header("⚙️ System Information")

    # Model parameters
    st.subheader("Model Parameters")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Bias Corrector:**")
        st.json({
            "shy_voter_weight": st.session_state.params.bias_corrector.shy_voter_weight,
            "min_poll_sample_size": st.session_state.params.bias_corrector.min_poll_sample_size
        })

        st.markdown("**FLB Adjuster:**")
        st.json({
            "favorite_threshold": st.session_state.params.flb_adjuster.favorite_threshold,
            "longshot_threshold": st.session_state.params.flb_adjuster.longshot_threshold
        })

        st.markdown("**RFR Adjuster:**")
        st.json({
            "risk_free_rate": st.session_state.params.rfr_adjuster.risk_free_rate,
            "min_probability_threshold": st.session_state.params.rfr_adjuster.min_probability_threshold
        })

    with col2:
        st.markdown("**Dutch Book Detector:**")
        st.json({
            "transaction_fee_per_share": st.session_state.params.dutchbook.transaction_fee_per_share
        })

        st.markdown("**Spatial Arb Detector:**")
        st.json({
            "total_fee_cost": st.session_state.params.spatial_arb.total_fee_cost,
            "min_net_profit_cents": st.session_state.params.spatial_arb.min_net_profit_cents
        })

    st.divider()

    # System status
    st.subheader("System Status")

    status_data = {
        "Component": ["Dashboard", "Kalshi Connector", "Polymarket Connector", "Analytical Modules"],
        "Status": ["✅ Running", "🟢 Connected" if st.session_state.kalshi.connected else "🔴 Offline",
                   "🟢 Connected" if st.session_state.polymarket.connected else "🔴 Offline", "✅ Loaded"],
        "Mode": ["Production", "Simulation", "Simulation", "Active"]
    }

    st.table(pd.DataFrame(status_data))

    st.divider()

    # About
    st.subheader("About The Oracle")
    st.markdown("""
    **The Oracle** is an institutional-grade prediction market analysis system
    that implements strategies used by the most successful traders including:

    - **Théo** ($50M+ profit) - Bias correction using the Neighbor Method
    - **Domer** ($400M+ volume) - Risk-free rate arbitrage and structural edges
    - **GCR** - Behavioral psychology and liquidity exploitation

    The system analyzes markets on Kalshi (regulated, fiat) and Polymarket (crypto, global)
    to find mispricing and generate alpha through:

    1. **Spatial Arbitrage**: Cross-venue price differences
    2. **Dutch Book**: Combinatorial market inefficiencies
    3. **Bias Correction**: Social desirability bias adjustment
    4. **Favorite-Longshot Bias**: Systematic mispricing patterns
    5. **Time-Value Analysis**: Risk-free rate arbitrage

    **Version**: 1.0.0
    **Last Updated**: November 2025
    """)

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.caption(f"The Oracle Dashboard | Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Running in simulation mode")

# Auto-refresh (optional)
# Uncomment to enable auto-refresh every 30 seconds
# time.sleep(30)
# st.rerun()
