#!/usr/bin/env python3
"""
The Oracle - Terminal Monitor
Watch the system in real-time from your terminal.

Usage:
    python3 terminal_monitor.py

Press Ctrl+C to exit
"""

import sqlite3
import time
import os
from datetime import datetime
from pathlib import Path

DB_PATH = "data/oracle_data.db"

def clear_screen():
    """Clear terminal screen."""
    os.system('clear' if os.name != 'nt' else 'cls')

def get_db_connection():
    """Connect to database."""
    if not Path(DB_PATH).exists():
        return None
    return sqlite3.connect(DB_PATH)

def format_time_ago(timestamp_str):
    """Format timestamp as 'X minutes ago'."""
    if not timestamp_str:
        return "Never"

    try:
        dt = datetime.fromisoformat(timestamp_str)
        delta = datetime.now() - dt
        minutes = int(delta.total_seconds() / 60)

        if minutes < 1:
            return "Just now"
        elif minutes == 1:
            return "1 min ago"
        elif minutes < 60:
            return f"{minutes} mins ago"
        else:
            hours = minutes // 60
            return f"{hours}h ago"
    except:
        return "Unknown"

def check_system_running():
    """Check if Oracle is running."""
    import subprocess
    try:
        result = subprocess.run(['pgrep', '-f', 'run_oracle_system'],
                              capture_output=True, text=True)
        return bool(result.stdout.strip())
    except:
        return False

def display_dashboard():
    """Display the terminal dashboard."""
    clear_screen()

    print("=" * 100)
    print(" " * 35 + "🔮 THE ORACLE - LIVE MONITOR")
    print("=" * 100)
    print(f"Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check if system is running
    is_running = check_system_running()
    if is_running:
        print("Status: ✅ RUNNING")
    else:
        print("Status: ⚠️  NOT RUNNING (Start with: python3 run_oracle_system.py --mode paper)")

    print("=" * 100)

    # Connect to database
    conn = get_db_connection()

    if conn is None:
        print("\n⚠️  Database not found. System may not have started yet.")
        print("\nWaiting for data collection to begin...")
        return

    cursor = conn.cursor()

    # ========================================================================
    # SYSTEM OVERVIEW
    # ========================================================================

    print("\n📊 SYSTEM OVERVIEW")
    print("-" * 100)

    # Total snapshots
    cursor.execute("SELECT COUNT(*) FROM market_snapshots")
    total_snapshots = cursor.fetchone()[0]

    # Total signals
    cursor.execute("SELECT COUNT(*) FROM signals")
    total_signals = cursor.fetchone()[0]

    # Active signals
    cursor.execute("SELECT COUNT(*) FROM signals WHERE status = 'active'")
    active_signals = cursor.fetchone()[0]

    # Closed signals
    cursor.execute("SELECT COUNT(*) FROM signals WHERE status = 'closed'")
    closed_signals = cursor.fetchone()[0]

    # Latest snapshot
    cursor.execute("SELECT MAX(timestamp) FROM market_snapshots")
    latest_snapshot = cursor.fetchone()[0]

    print(f"Total Snapshots: {total_snapshots:,}  |  ", end="")
    print(f"Total Signals: {total_signals}  |  ", end="")
    print(f"Active: {active_signals}  |  ", end="")
    print(f"Closed: {closed_signals}  |  ", end="")
    print(f"Last Data: {format_time_ago(latest_snapshot)}")

    # ========================================================================
    # PERFORMANCE (Last 24h)
    # ========================================================================

    print("\n📈 PERFORMANCE (Last 24 Hours)")
    print("-" * 100)

    # Signals generated
    cursor.execute("""
        SELECT COUNT(*) FROM signals
        WHERE timestamp > datetime('now', '-1 day')
    """)
    signals_24h = cursor.fetchone()[0]

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
    win_rate = (result[0] / result[1] * 100) if result[1] > 0 else 0

    # Average edge
    cursor.execute("""
        SELECT AVG(edge_cents)
        FROM signals
        WHERE timestamp > datetime('now', '-1 day')
    """)
    avg_edge = cursor.fetchone()[0] or 0

    # Total P&L
    cursor.execute("""
        SELECT SUM(profit_loss)
        FROM signals
        WHERE status = 'closed'
        AND timestamp > datetime('now', '-1 day')
    """)
    total_pnl = cursor.fetchone()[0] or 0

    print(f"Signals: {signals_24h}  |  ", end="")
    print(f"Win Rate: {win_rate:.1f}%  |  ", end="")
    print(f"Avg Edge: {avg_edge:.2f}¢  |  ", end="")
    print(f"P&L: {total_pnl:+.2f}¢")

    # ========================================================================
    # RECENT SIGNALS
    # ========================================================================

    print("\n🎯 RECENT SIGNALS (Last 10)")
    print("-" * 100)

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
        LIMIT 10
    """)

    signals = cursor.fetchall()

    if signals:
        # Header
        print(f"{'ID':<5} {'Time':<12} {'Strategy':<20} {'Market':<25} {'Signal':<6} {'Edge':<8} {'Conv':<6} {'Status':<8} {'P&L':<10}")
        print("-" * 100)

        for signal in signals:
            sig_id, timestamp, strategy, market, sig_type, edge, conviction, status, pnl = signal

            # Format timestamp
            dt = datetime.fromisoformat(timestamp)
            time_str = dt.strftime('%m/%d %H:%M')

            # Truncate long names
            strategy = strategy[:20]
            market = market[:25]

            # Format P&L
            pnl_str = f"{pnl:+.2f}¢" if pnl is not None else "N/A"

            # Conviction color
            if conviction == 'HIGH':
                conv_str = '🟢 HIGH'
            elif conviction == 'MEDIUM':
                conv_str = '🟡 MED'
            else:
                conv_str = '🟠 LOW'

            print(f"{sig_id:<5} {time_str:<12} {strategy:<20} {market:<25} {sig_type:<6} {edge:<8.2f} {conv_str:<6} {status:<8} {pnl_str:<10}")
    else:
        print("No signals yet. System is collecting data and building price history...")
        print("First signals typically appear 10-15 minutes after startup.")

    # ========================================================================
    # ACTIVE SIGNALS DETAIL
    # ========================================================================

    if active_signals > 0:
        print("\n🔥 ACTIVE SIGNALS")
        print("-" * 100)

        cursor.execute("""
            SELECT
                id,
                timestamp,
                strategy,
                market_name,
                signal_type,
                edge_cents,
                entry_price,
                current_price,
                profit_loss
            FROM signals
            WHERE status = 'active'
            ORDER BY timestamp DESC
        """)

        active = cursor.fetchall()

        # Header
        print(f"{'ID':<5} {'Opened':<12} {'Strategy':<20} {'Market':<25} {'Signal':<6} {'Entry':<8} {'Current':<8} {'P&L':<10}")
        print("-" * 100)

        for sig in active:
            sig_id, timestamp, strategy, market, sig_type, edge, entry, current, pnl = sig

            dt = datetime.fromisoformat(timestamp)
            time_str = dt.strftime('%m/%d %H:%M')

            strategy = strategy[:20]
            market = market[:25]

            entry_str = f"{entry:.2f}¢" if entry else "N/A"
            current_str = f"{current:.2f}¢" if current else "N/A"
            pnl_str = f"{pnl:+.2f}¢" if pnl is not None else "N/A"

            print(f"{sig_id:<5} {time_str:<12} {strategy:<20} {market:<25} {sig_type:<6} {entry_str:<8} {current_str:<8} {pnl_str:<10}")

    # ========================================================================
    # DATA COLLECTION
    # ========================================================================

    print("\n🔄 DATA COLLECTION")
    print("-" * 100)

    # Snapshots by exchange
    cursor.execute("""
        SELECT exchange, COUNT(*) as count
        FROM market_snapshots
        GROUP BY exchange
    """)
    exchange_data = cursor.fetchall()

    for exchange, count in exchange_data:
        print(f"{exchange.title()}: {count:,} snapshots  |  ", end="")

    print()

    # ========================================================================
    # FOOTER
    # ========================================================================

    print("\n" + "=" * 100)
    print("🔮 PAPER MODE | Data: Every 5min | Signals: Every 10min | ML: Every hour | Ctrl+C to exit")
    print("=" * 100)

    conn.close()

def main():
    """Main monitoring loop."""
    print("Starting Oracle Terminal Monitor...")
    print("Press Ctrl+C to exit\n")
    time.sleep(2)

    try:
        while True:
            display_dashboard()
            time.sleep(30)  # Refresh every 30 seconds
    except KeyboardInterrupt:
        print("\n\n👋 Monitor stopped. Oracle continues running in background.")
        print("   To stop Oracle: pkill -f run_oracle_system")

if __name__ == "__main__":
    main()
