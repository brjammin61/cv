#!/usr/bin/env python3
"""
Quick Status Check - Run this anytime to see Oracle status in the terminal
"""

import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path

DB_PATH = "data/oracle_data.db"

print("\n" + "=" * 80)
print("🔮 THE ORACLE - QUICK STATUS CHECK")
print("=" * 80)
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# Check if Oracle is running
try:
    result = subprocess.run(['pgrep', '-f', 'run_oracle_system'],
                          capture_output=True, text=True, timeout=5)
    is_running = bool(result.stdout.strip())

    if is_running:
        pid = result.stdout.strip()
        print(f"\n✅ Oracle System: RUNNING (PID: {pid})")
    else:
        print(f"\n❌ Oracle System: NOT RUNNING")
        print("   Start it with: python3 run_oracle_system.py --mode paper")
except Exception as e:
    print(f"\n⚠️  Could not check system status: {e}")

print("=" * 80)

# Check database
if not Path(DB_PATH).exists():
    print("\n⚠️  Database not found - system hasn't started collecting data yet")
    print("=" * 80)
    exit(0)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Quick metrics
cursor.execute("SELECT COUNT(*) FROM market_snapshots")
snapshots = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM signals")
signals = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM signals WHERE status = 'active'")
active = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM signals WHERE status = 'closed'")
closed = cursor.fetchone()[0]

print(f"\n📊 QUICK STATS:")
print(f"   Snapshots: {snapshots:,} | Signals: {signals} | Active: {active} | Closed: {closed}")

# Win rate if we have closed signals
if closed > 0:
    cursor.execute("""
        SELECT
            COUNT(CASE WHEN profit_loss > 0 THEN 1 END) as wins,
            COUNT(*) as total,
            AVG(profit_loss) as avg_pnl
        FROM signals
        WHERE status = 'closed'
    """)
    wins, total, avg_pnl = cursor.fetchone()
    win_rate = (wins / total) * 100
    print(f"   Win Rate: {win_rate:.1f}% ({wins}/{total}) | Avg P&L: {avg_pnl:+.2f}¢")

# Recent activity
cursor.execute("""
    SELECT timestamp FROM signals
    ORDER BY timestamp DESC LIMIT 1
""")
result = cursor.fetchone()
if result:
    last_signal = datetime.fromisoformat(result[0])
    mins_ago = int((datetime.now() - last_signal).total_seconds() / 60)
    print(f"   Last Signal: {mins_ago} minutes ago")
else:
    print(f"   Last Signal: Never")

cursor.execute("SELECT MAX(timestamp) FROM market_snapshots")
result = cursor.fetchone()
if result and result[0]:
    last_collection = datetime.fromisoformat(result[0])
    mins_ago = int((datetime.now() - last_collection).total_seconds() / 60)
    print(f"   Last Data Collection: {mins_ago} minutes ago")
else:
    print(f"   Last Data Collection: Never")

print("=" * 80)

# Most recent signals
print(f"\n🎯 LATEST SIGNALS (Last 5):")
cursor.execute("""
    SELECT
        timestamp,
        strategy,
        edge_cents,
        conviction,
        status,
        profit_loss
    FROM signals
    ORDER BY timestamp DESC
    LIMIT 5
""")

signals_list = cursor.fetchall()
if signals_list:
    for sig in signals_list:
        ts = datetime.fromisoformat(sig[0]).strftime('%m/%d %H:%M')
        strategy = sig[1][:20]
        edge = sig[2]
        conv = sig[3]
        status = sig[4]
        pnl = sig[5] if sig[5] is not None else 0

        status_icon = "🟢" if status == "closed" and pnl > 0 else "🔴" if status == "closed" and pnl < 0 else "⏳"
        print(f"   {status_icon} {ts} | {strategy:<20} | {edge:+.1f}¢ | {conv:<6} | {pnl:+.1f}¢")
else:
    print("   No signals yet - collecting data...")

print("=" * 80)

conn.close()

print("\nℹ️  Run this anytime: python3 status.py")
print("ℹ️  Full dashboard: streamlit run live_monitor.py")
print("=" * 80 + "\n")
