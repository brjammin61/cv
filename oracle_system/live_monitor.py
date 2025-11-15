#!/usr/bin/env python3
"""
The Oracle - Live Monitoring Dashboard

Real-time view of the Oracle system in action.
Auto-refreshes every 30 seconds to show latest data.

Usage:
    streamlit run live_monitor.py
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import time
from pathlib import Path

# Page config
st.set_page_config(
    page_title="Oracle Live Monitor",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Database path
DB_PATH = "data/oracle_data.db"

# Auto-refresh every 30 seconds
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()

# Title
st.title("🔮 The Oracle - Live System Monitor")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Auto-refresh countdown
refresh_interval = 30  # seconds
time_since_update = (datetime.now() - st.session_state.last_update).total_seconds()
if time_since_update >= refresh_interval:
    st.session_state.last_update = datetime.now()
    st.rerun()

st.progress(min(time_since_update / refresh_interval, 1.0))
st.caption(f"Auto-refresh in {max(0, int(refresh_interval - time_since_update))}s")

# Check if system is running
import subprocess
try:
    result = subprocess.run(['pgrep', '-f', 'run_oracle_system'], capture_output=True, text=True)
    is_running = bool(result.stdout.strip())
except:
    is_running = False

if is_running:
    st.success("✅ Oracle System: RUNNING")
else:
    st.error("❌ Oracle System: NOT RUNNING")

st.divider()

# Connect to database
def get_db_connection():
    if not Path(DB_PATH).exists():
        return None
    return sqlite3.connect(DB_PATH)

conn = get_db_connection()

if conn is None:
    st.warning("⚠️ Database not found. System may not have started collecting data yet.")
    st.stop()

# ============================================================================
# SYSTEM OVERVIEW
# ============================================================================

st.header("📊 System Overview")

col1, col2, col3, col4 = st.columns(4)

# Total snapshots
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM market_snapshots")
total_snapshots = cursor.fetchone()[0]

col1.metric("Total Snapshots", f"{total_snapshots:,}")

# Total signals
cursor.execute("SELECT COUNT(*) FROM signals")
total_signals = cursor.fetchone()[0]

col2.metric("Total Signals", total_signals)

# Active signals
cursor.execute("SELECT COUNT(*) FROM signals WHERE status = 'active'")
active_signals = cursor.fetchone()[0]

col3.metric("Active Signals", active_signals)

# Closed signals
cursor.execute("SELECT COUNT(*) FROM signals WHERE status = 'closed'")
closed_signals = cursor.fetchone()[0]

col4.metric("Closed Signals", closed_signals)

st.divider()

# ============================================================================
# PERFORMANCE METRICS (Last 24h)
# ============================================================================

st.header("📈 Performance (Last 24 Hours)")

col1, col2, col3, col4 = st.columns(4)

# Signals last 24h
cursor.execute("""
    SELECT COUNT(*) FROM signals
    WHERE timestamp > datetime('now', '-1 day')
""")
signals_24h = cursor.fetchone()[0]
col1.metric("Signals Generated", signals_24h)

# Win rate
cursor.execute("""
    SELECT
        COUNT(CASE WHEN profit_loss > 0 THEN 1 END) as wins,
        COUNT(*) as total
    FROM signals
    WHERE status = 'closed'
    AND timestamp > datetime('now', '-1 day')
""")
result = cursor.fetchone()
if result[1] > 0:
    win_rate = (result[0] / result[1]) * 100
    col2.metric("Win Rate", f"{win_rate:.1f}%")
else:
    col2.metric("Win Rate", "N/A")

# Average edge
cursor.execute("""
    SELECT AVG(edge_cents)
    FROM signals
    WHERE timestamp > datetime('now', '-1 day')
""")
avg_edge = cursor.fetchone()[0] or 0
col3.metric("Avg Edge", f"{avg_edge:.2f}¢")

# Total P&L (closed signals)
cursor.execute("""
    SELECT SUM(profit_loss)
    FROM signals
    WHERE status = 'closed'
    AND timestamp > datetime('now', '-1 day')
""")
total_pnl = cursor.fetchone()[0] or 0
col4.metric("Total P&L", f"{total_pnl:+.2f}¢", delta=f"{total_pnl:.2f}¢")

st.divider()

# ============================================================================
# RECENT SIGNALS
# ============================================================================

st.header("🎯 Recent Signals (Last 20)")

cursor.execute("""
    SELECT
        id,
        timestamp,
        strategy,
        market_name,
        signal_type,
        edge_cents,
        conviction,
        status,
        profit_loss
    FROM signals
    ORDER BY timestamp DESC
    LIMIT 20
""")

signals_data = cursor.fetchall()

if signals_data:
    df_signals = pd.DataFrame(signals_data, columns=[
        'ID', 'Timestamp', 'Strategy', 'Market', 'Signal',
        'Edge (¢)', 'Conviction', 'Status', 'P&L (¢)'
    ])

    # Format timestamp
    df_signals['Timestamp'] = pd.to_datetime(df_signals['Timestamp']).dt.strftime('%m/%d %H:%M')

    # Color code by conviction
    def color_conviction(val):
        if val == 'HIGH':
            return 'background-color: #90EE90'
        elif val == 'MEDIUM':
            return 'background-color: #FFD700'
        else:
            return 'background-color: #FFA07A'

    # Color code P&L
    def color_pnl(val):
        if pd.isna(val) or val is None:
            return ''
        if val > 0:
            return 'background-color: #90EE90'
        elif val < 0:
            return 'background-color: #FFA07A'
        return ''

    styled_df = df_signals.style.applymap(color_conviction, subset=['Conviction'])
    styled_df = styled_df.applymap(color_pnl, subset=['P&L (¢)'])

    st.dataframe(styled_df, use_container_width=True, height=400)
else:
    st.info("No signals generated yet. System is collecting data...")

st.divider()

# ============================================================================
# SIGNAL DISTRIBUTION
# ============================================================================

col1, col2 = st.columns(2)

with col1:
    st.subheader("Signals by Strategy")

    cursor.execute("""
        SELECT strategy, COUNT(*) as count
        FROM signals
        GROUP BY strategy
        ORDER BY count DESC
    """)

    strategy_data = cursor.fetchall()

    if strategy_data:
        df_strategy = pd.DataFrame(strategy_data, columns=['Strategy', 'Count'])
        st.bar_chart(df_strategy.set_index('Strategy'))
    else:
        st.info("No signals yet")

with col2:
    st.subheader("Signals by Conviction")

    cursor.execute("""
        SELECT conviction, COUNT(*) as count
        FROM signals
        GROUP BY conviction
        ORDER BY
            CASE conviction
                WHEN 'HIGH' THEN 1
                WHEN 'MEDIUM' THEN 2
                WHEN 'LOW' THEN 3
            END
    """)

    conviction_data = cursor.fetchall()

    if conviction_data:
        df_conviction = pd.DataFrame(conviction_data, columns=['Conviction', 'Count'])
        st.bar_chart(df_conviction.set_index('Conviction'))
    else:
        st.info("No signals yet")

st.divider()

# ============================================================================
# DATA COLLECTION STATS
# ============================================================================

st.header("🔄 Data Collection")

col1, col2, col3 = st.columns(3)

# Snapshots by exchange
cursor.execute("""
    SELECT exchange, COUNT(*) as count
    FROM market_snapshots
    GROUP BY exchange
""")
exchange_data = cursor.fetchall()

if exchange_data:
    for exchange, count in exchange_data:
        if exchange == 'kalshi':
            col1.metric("Kalshi Snapshots", f"{count:,}")
        elif exchange == 'polymarket':
            col2.metric("Polymarket Snapshots", f"{count:,}")

# Latest snapshot time
cursor.execute("SELECT MAX(timestamp) FROM market_snapshots")
latest_snapshot = cursor.fetchone()[0]

if latest_snapshot:
    latest_time = datetime.fromisoformat(latest_snapshot)
    time_ago = datetime.now() - latest_time
    minutes_ago = int(time_ago.total_seconds() / 60)

    col3.metric("Last Snapshot", f"{minutes_ago}m ago")
else:
    col3.metric("Last Snapshot", "Never")

st.divider()

# ============================================================================
# ACTIVE SIGNALS DETAIL
# ============================================================================

if active_signals > 0:
    st.header("🔥 Active Signals")

    cursor.execute("""
        SELECT
            id,
            timestamp,
            strategy,
            market_name,
            signal_type,
            edge_cents,
            conviction,
            entry_price,
            current_price,
            profit_loss
        FROM signals
        WHERE status = 'active'
        ORDER BY timestamp DESC
    """)

    active_data = cursor.fetchall()

    if active_data:
        df_active = pd.DataFrame(active_data, columns=[
            'ID', 'Opened', 'Strategy', 'Market', 'Signal',
            'Edge (¢)', 'Conviction', 'Entry', 'Current', 'P&L (¢)'
        ])

        df_active['Opened'] = pd.to_datetime(df_active['Opened']).dt.strftime('%m/%d %H:%M')

        st.dataframe(df_active, use_container_width=True)

st.divider()

# ============================================================================
# SYSTEM LOGS (Latest)
# ============================================================================

st.header("📝 Recent System Activity")

log_file = Path("logs/oracle_system.log")

if log_file.exists():
    with open(log_file, 'r') as f:
        lines = f.readlines()
        recent_logs = lines[-50:]  # Last 50 lines

    # Show only INFO and above
    filtered_logs = [line for line in recent_logs if any(
        level in line for level in ['INFO', 'WARNING', 'ERROR']
    )]

    log_text = ''.join(filtered_logs[-20:])  # Last 20 relevant lines
    st.code(log_text, language='log')
else:
    st.info("No logs available yet")

# Close database connection
conn.close()

# Footer
st.divider()
st.caption(f"""
🔮 **The Oracle System** | Running in PAPER mode |
Data updates every 5 minutes | Signals every 10 minutes | ML optimization every hour
""")
