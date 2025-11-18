#!/usr/bin/env python3
"""
The Oracle - Web Dashboard
Beautiful live dashboard accessible from any browser.

Usage:
    python3 web_dashboard.py

Then access at: http://your-server-ip:8080
"""

from flask import Flask, render_template, jsonify
import sqlite3
from datetime import datetime
from pathlib import Path
import subprocess

app = Flask(__name__)
DB_PATH = "data/oracle_data.db"

def get_db_connection():
    """Connect to database."""
    if not Path(DB_PATH).exists():
        return None
    return sqlite3.connect(DB_PATH)

def check_system_running():
    """Check if Oracle is running."""
    try:
        result = subprocess.run(['pgrep', '-f', 'run_oracle_system'],
                              capture_output=True, text=True)
        return bool(result.stdout.strip())
    except:
        return False

@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('dashboard.html')

@app.route('/api/status')
def api_status():
    """Get current system status."""
    conn = get_db_connection()

    if conn is None:
        return jsonify({
            'error': 'Database not found',
            'running': check_system_running()
        })

    cursor = conn.cursor()

    # System overview
    cursor.execute('SELECT COUNT(*) FROM market_snapshots')
    total_snapshots = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM signals')
    total_signals = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM signals WHERE status = "active"')
    active_signals = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM signals WHERE status = "closed"')
    closed_signals = cursor.fetchone()[0]

    cursor.execute('SELECT MAX(timestamp) FROM market_snapshots')
    last_snapshot = cursor.fetchone()[0]

    # Performance metrics
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN profit_loss > 0 THEN 1 END) as wins,
            AVG(edge_cents) as avg_edge,
            SUM(profit_loss) as pnl
        FROM signals
        WHERE status = 'closed' AND timestamp > datetime('now', '-1 day')
    """)
    perf = cursor.fetchone()
    total_closed, wins, avg_edge, pnl = perf
    win_rate = (wins / total_closed * 100) if total_closed > 0 else 0

    # Signals in last 24h
    cursor.execute("""
        SELECT COUNT(*) FROM signals
        WHERE timestamp > datetime('now', '-1 day')
    """)
    signals_24h = cursor.fetchone()[0]

    conn.close()

    return jsonify({
        'running': check_system_running(),
        'timestamp': datetime.now().isoformat(),
        'overview': {
            'total_snapshots': total_snapshots,
            'total_signals': total_signals,
            'active_signals': active_signals,
            'closed_signals': closed_signals,
            'last_snapshot': last_snapshot
        },
        'performance': {
            'signals_24h': signals_24h,
            'win_rate': round(win_rate, 1),
            'avg_edge': round(avg_edge or 0, 2),
            'total_pnl': round(pnl or 0, 2)
        }
    })

@app.route('/api/signals')
def api_signals():
    """Get recent signals."""
    conn = get_db_connection()

    if conn is None:
        return jsonify({'error': 'Database not found'})

    cursor = conn.cursor()

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

    signals = []
    for row in cursor.fetchall():
        signals.append({
            'id': row[0],
            'timestamp': row[1],
            'strategy': row[2],
            'market': row[3],
            'signal_type': row[4],
            'edge': round(row[5], 2),
            'conviction': row[6],
            'status': row[7],
            'pnl': round(row[8], 2) if row[8] is not None else None
        })

    conn.close()

    return jsonify({'signals': signals})

@app.route('/api/active')
def api_active():
    """Get active signals."""
    conn = get_db_connection()

    if conn is None:
        return jsonify({'error': 'Database not found'})

    cursor = conn.cursor()

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

    active = []
    for row in cursor.fetchall():
        active.append({
            'id': row[0],
            'timestamp': row[1],
            'strategy': row[2],
            'market': row[3],
            'signal_type': row[4],
            'edge': round(row[5], 2),
            'conviction': row[6],
            'entry_price': row[7],
            'current_price': row[8],
            'pnl': round(row[9], 2) if row[9] is not None else None
        })

    conn.close()

    return jsonify({'active': active})

@app.route('/api/charts')
def api_charts():
    """Get chart data."""
    conn = get_db_connection()

    if conn is None:
        return jsonify({'error': 'Database not found'})

    cursor = conn.cursor()

    # Signals by strategy
    cursor.execute("""
        SELECT strategy, COUNT(*) as count
        FROM signals
        GROUP BY strategy
        ORDER BY count DESC
    """)
    by_strategy = [{'strategy': row[0], 'count': row[1]} for row in cursor.fetchall()]

    # Signals by conviction
    cursor.execute("""
        SELECT conviction, COUNT(*) as count
        FROM signals
        GROUP BY conviction
    """)
    by_conviction = [{'conviction': row[0], 'count': row[1]} for row in cursor.fetchall()]

    # P&L over time (last 24h)
    cursor.execute("""
        SELECT
            datetime(timestamp) as time,
            SUM(profit_loss) OVER (ORDER BY timestamp) as cumulative_pnl
        FROM signals
        WHERE status = 'closed' AND timestamp > datetime('now', '-1 day')
        ORDER BY timestamp
    """)
    pnl_series = [{'time': row[0], 'pnl': round(row[1], 2)} for row in cursor.fetchall()]

    conn.close()

    return jsonify({
        'by_strategy': by_strategy,
        'by_conviction': by_conviction,
        'pnl_series': pnl_series
    })

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    Path('templates').mkdir(exist_ok=True)

    print("=" * 80)
    print("🔮 THE ORACLE - WEB DASHBOARD")
    print("=" * 80)
    print("\nStarting web server...")
    print("\nAccess dashboard at:")
    print("  → http://localhost:8080")
    print("  → http://YOUR_SERVER_IP:8080")
    print("\nPress Ctrl+C to stop")
    print("=" * 80)

    app.run(host='0.0.0.0', port=8080, debug=False)
