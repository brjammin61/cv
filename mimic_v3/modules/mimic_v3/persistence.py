"""
Persistence.py - SQLite Data Persistence Layer
MIMIC V3.1 HARDENED

Implements:
- P.1.1: Persistent Shadow ID mapping (survives reboots)
- P.1.2: Trade history with position tracking
- P.1.3: Whale performance statistics
- P.1.4: System state recovery
"""

import sqlite3
import datetime
import logging
import json
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from contextlib import contextmanager
import threading


@dataclass
class WhaleRecord:
    """Persistent whale profile"""
    hash_id: str
    friendly_id: str
    first_seen: datetime.datetime
    total_volume: float
    total_trades: int
    winning_trades: int
    total_pnl: float
    win_rate: float
    avg_size: float
    last_seen: datetime.datetime


@dataclass
class TradeRecord:
    """Persistent trade record"""
    trade_id: str
    shadow_id: str
    ticker: str
    event_ticker: str
    side: str
    size_usd: float
    contracts: int
    entry_price: float
    exit_price: Optional[float]
    pnl: Optional[float]
    status: str  # 'OPEN', 'CLOSED', 'CANCELLED'
    strategy_type: str
    win_prob: float
    timestamp: datetime.datetime
    closed_at: Optional[datetime.datetime]


class MimicDB:
    """
    SQLite persistence layer for MIMIC V3.1.

    Thread-safe with connection pooling.
    Stores:
    - Shadow whale mappings and statistics
    - Complete trade history
    - System state for recovery
    """

    def __init__(self, db_path: str = "data/mimic_data.db", logger: logging.Logger = None):
        self.db_path = db_path
        self.logger = logger or logging.getLogger(__name__)
        self._local = threading.local()

        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)

        # Initialize tables
        self._init_tables()
        self.logger.info("PERSISTENCE: SQLite Connected")

    def _get_conn(self) -> sqlite3.Connection:
        """Get thread-local connection"""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    @contextmanager
    def _cursor(self):
        """Context manager for cursor with auto-commit"""
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Database error: {e}")
            raise

    def _init_tables(self):
        """Initialize all database tables"""
        with self._cursor() as cursor:
            # P.1.1: Persistent Shadow Whale Mapping
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS shadow_whales (
                    hash_id TEXT PRIMARY KEY,
                    friendly_id TEXT UNIQUE NOT NULL,
                    first_seen TIMESTAMP NOT NULL,
                    last_seen TIMESTAMP NOT NULL,
                    total_volume REAL DEFAULT 0,
                    total_trades INTEGER DEFAULT 0,
                    winning_trades INTEGER DEFAULT 0,
                    total_pnl REAL DEFAULT 0,
                    win_rate REAL DEFAULT 0.5,
                    avg_size REAL DEFAULT 0,
                    strategy_counts TEXT DEFAULT '{}',
                    metadata TEXT DEFAULT '{}'
                )
            ''')

            # P.1.2: Trade History Persistence
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trade_history (
                    trade_id TEXT PRIMARY KEY,
                    shadow_id TEXT NOT NULL,
                    ticker TEXT NOT NULL,
                    event_ticker TEXT,
                    side TEXT NOT NULL,
                    size_usd REAL NOT NULL,
                    contracts INTEGER DEFAULT 1,
                    entry_price REAL NOT NULL,
                    exit_price REAL,
                    pnl REAL,
                    status TEXT DEFAULT 'OPEN',
                    strategy_type TEXT,
                    win_prob REAL,
                    features TEXT,
                    timestamp TIMESTAMP NOT NULL,
                    closed_at TIMESTAMP,
                    FOREIGN KEY (shadow_id) REFERENCES shadow_whales(friendly_id)
                )
            ''')

            # P.1.3: Daily Performance Snapshots
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_snapshots (
                    date TEXT PRIMARY KEY,
                    starting_capital REAL,
                    ending_capital REAL,
                    daily_pnl REAL,
                    trades_taken INTEGER,
                    wins INTEGER,
                    losses INTEGER,
                    max_drawdown REAL,
                    metadata TEXT DEFAULT '{}'
                )
            ''')

            # P.1.4: System State (for recovery)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_state (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP
                )
            ''')

            # Create indices for common queries
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_status ON trade_history(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_ticker ON trade_history(ticker)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trade_history(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_whales_winrate ON shadow_whales(win_rate)')

        self.logger.info("PERSISTENCE: Tables initialized")

    # ==================== SHADOW WHALE METHODS ====================

    def get_or_create_shadow_id(self, raw_hash: str, volume: float = 0) -> str:
        """
        Resolves a raw hash to a persistent Friendly ID.
        Creates new whale record if not exists.

        Args:
            raw_hash: MD5 hash from scanner fingerprinting
            volume: Initial trade volume

        Returns:
            Friendly ID (e.g., "Whale_0001")
        """
        with self._cursor() as cursor:
            # Check if exists
            cursor.execute(
                "SELECT friendly_id FROM shadow_whales WHERE hash_id = ?",
                (raw_hash,)
            )
            row = cursor.fetchone()

            if row:
                # Update last_seen
                cursor.execute(
                    "UPDATE shadow_whales SET last_seen = ? WHERE hash_id = ?",
                    (datetime.datetime.utcnow(), raw_hash)
                )
                return row['friendly_id']

            # Create new whale ID
            cursor.execute("SELECT COUNT(*) as cnt FROM shadow_whales")
            count = cursor.fetchone()['cnt']
            friendly_id = f"Whale_{count + 1:04d}"

            now = datetime.datetime.utcnow()
            cursor.execute('''
                INSERT INTO shadow_whales
                (hash_id, friendly_id, first_seen, last_seen, total_volume)
                VALUES (?, ?, ?, ?, ?)
            ''', (raw_hash, friendly_id, now, now, volume))

            self.logger.info(f"PERSISTENCE: New whale registered: {friendly_id}")
            return friendly_id

    def update_whale_stats(
        self,
        friendly_id: str,
        volume: float,
        is_win: bool,
        pnl: float,
        strategy_type: str = None
    ):
        """Update whale statistics after trade settlement"""
        with self._cursor() as cursor:
            # Get current stats
            cursor.execute(
                "SELECT * FROM shadow_whales WHERE friendly_id = ?",
                (friendly_id,)
            )
            row = cursor.fetchone()

            if not row:
                self.logger.warning(f"Whale not found: {friendly_id}")
                return

            # Calculate new stats
            new_total_trades = row['total_trades'] + 1
            new_winning_trades = row['winning_trades'] + (1 if is_win else 0)
            new_total_volume = row['total_volume'] + volume
            new_total_pnl = row['total_pnl'] + pnl
            new_win_rate = new_winning_trades / new_total_trades
            new_avg_size = new_total_volume / new_total_trades

            # Update strategy counts
            strategy_counts = json.loads(row['strategy_counts'] or '{}')
            if strategy_type:
                strategy_counts[strategy_type] = strategy_counts.get(strategy_type, 0) + 1

            cursor.execute('''
                UPDATE shadow_whales SET
                    total_trades = ?,
                    winning_trades = ?,
                    total_volume = ?,
                    total_pnl = ?,
                    win_rate = ?,
                    avg_size = ?,
                    strategy_counts = ?,
                    last_seen = ?
                WHERE friendly_id = ?
            ''', (
                new_total_trades, new_winning_trades, new_total_volume,
                new_total_pnl, new_win_rate, new_avg_size,
                json.dumps(strategy_counts), datetime.datetime.utcnow(),
                friendly_id
            ))

    def get_whale_stats(self, friendly_id: str) -> Optional[Dict]:
        """Get whale statistics"""
        with self._cursor() as cursor:
            cursor.execute(
                "SELECT * FROM shadow_whales WHERE friendly_id = ?",
                (friendly_id,)
            )
            row = cursor.fetchone()

            if not row:
                return None

            return {
                "hash_id": row['hash_id'],
                "friendly_id": row['friendly_id'],
                "first_seen": row['first_seen'],
                "last_seen": row['last_seen'],
                "total_trades": row['total_trades'],
                "winning_trades": row['winning_trades'],
                "win_rate": row['win_rate'],
                "total_volume": row['total_volume'],
                "total_pnl": row['total_pnl'],
                "avg_size": row['avg_size'],
                "strategy_counts": json.loads(row['strategy_counts'] or '{}')
            }

    def get_top_whales(self, limit: int = 20, min_trades: int = 5) -> List[Dict]:
        """Get top performing whales by win rate"""
        with self._cursor() as cursor:
            cursor.execute('''
                SELECT * FROM shadow_whales
                WHERE total_trades >= ?
                ORDER BY win_rate DESC, total_pnl DESC
                LIMIT ?
            ''', (min_trades, limit))

            return [dict(row) for row in cursor.fetchall()]

    # ==================== TRADE HISTORY METHODS ====================

    def log_trade_open(
        self,
        trade_id: str,
        shadow_id: str,
        ticker: str,
        event_ticker: str,
        side: str,
        size_usd: float,
        contracts: int,
        entry_price: float,
        strategy_type: str,
        win_prob: float,
        features: Dict = None
    ):
        """Log a new trade opening"""
        with self._cursor() as cursor:
            cursor.execute('''
                INSERT INTO trade_history
                (trade_id, shadow_id, ticker, event_ticker, side, size_usd,
                 contracts, entry_price, status, strategy_type, win_prob,
                 features, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', ?, ?, ?, ?)
            ''', (
                trade_id, shadow_id, ticker, event_ticker, side, size_usd,
                contracts, entry_price, strategy_type, win_prob,
                json.dumps(features) if features else None,
                datetime.datetime.utcnow()
            ))

        self.logger.info(f"PERSISTENCE: Trade opened - {trade_id}")

    def log_trade_close(
        self,
        trade_id: str,
        exit_price: float,
        pnl: float,
        status: str = 'CLOSED'
    ):
        """Log trade closure with P&L"""
        with self._cursor() as cursor:
            cursor.execute('''
                UPDATE trade_history SET
                    exit_price = ?,
                    pnl = ?,
                    status = ?,
                    closed_at = ?
                WHERE trade_id = ?
            ''', (exit_price, pnl, status, datetime.datetime.utcnow(), trade_id))

        self.logger.info(f"PERSISTENCE: Trade closed - {trade_id} | PnL: ${pnl:.2f}")

    def get_open_positions(self) -> List[Dict]:
        """Get all open positions (for recovery)"""
        with self._cursor() as cursor:
            cursor.execute('''
                SELECT * FROM trade_history
                WHERE status = 'OPEN'
                ORDER BY timestamp DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]

    def get_trade_history(
        self,
        limit: int = 100,
        ticker: str = None,
        shadow_id: str = None
    ) -> List[Dict]:
        """Get trade history with optional filters"""
        with self._cursor() as cursor:
            query = "SELECT * FROM trade_history WHERE 1=1"
            params = []

            if ticker:
                query += " AND ticker = ?"
                params.append(ticker)
            if shadow_id:
                query += " AND shadow_id = ?"
                params.append(shadow_id)

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_performance_stats(self, days: int = 30) -> Dict:
        """Get performance statistics for last N days"""
        with self._cursor() as cursor:
            cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=days)

            cursor.execute('''
                SELECT
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN pnl <= 0 THEN 1 ELSE 0 END) as losses,
                    SUM(pnl) as total_pnl,
                    AVG(pnl) as avg_pnl,
                    MAX(pnl) as best_trade,
                    MIN(pnl) as worst_trade,
                    AVG(size_usd) as avg_size
                FROM trade_history
                WHERE status = 'CLOSED' AND timestamp >= ?
            ''', (cutoff,))

            row = cursor.fetchone()
            if not row or row['total_trades'] == 0:
                return {"total_trades": 0}

            return {
                "total_trades": row['total_trades'],
                "wins": row['wins'] or 0,
                "losses": row['losses'] or 0,
                "win_rate": (row['wins'] or 0) / row['total_trades'],
                "total_pnl": row['total_pnl'] or 0,
                "avg_pnl": row['avg_pnl'] or 0,
                "best_trade": row['best_trade'] or 0,
                "worst_trade": row['worst_trade'] or 0,
                "avg_size": row['avg_size'] or 0
            }

    # ==================== SYSTEM STATE METHODS ====================

    def save_state(self, key: str, value: any):
        """Save system state for recovery"""
        with self._cursor() as cursor:
            cursor.execute('''
                INSERT OR REPLACE INTO system_state (key, value, updated_at)
                VALUES (?, ?, ?)
            ''', (key, json.dumps(value), datetime.datetime.utcnow()))

    def load_state(self, key: str, default: any = None) -> any:
        """Load system state"""
        with self._cursor() as cursor:
            cursor.execute(
                "SELECT value FROM system_state WHERE key = ?",
                (key,)
            )
            row = cursor.fetchone()
            if row:
                return json.loads(row['value'])
            return default

    def save_daily_snapshot(
        self,
        starting_capital: float,
        ending_capital: float,
        daily_pnl: float,
        trades_taken: int,
        wins: int,
        losses: int,
        max_drawdown: float
    ):
        """Save daily performance snapshot"""
        today = datetime.date.today().isoformat()

        with self._cursor() as cursor:
            cursor.execute('''
                INSERT OR REPLACE INTO daily_snapshots
                (date, starting_capital, ending_capital, daily_pnl,
                 trades_taken, wins, losses, max_drawdown)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                today, starting_capital, ending_capital, daily_pnl,
                trades_taken, wins, losses, max_drawdown
            ))

    # ==================== UTILITY METHODS ====================

    def vacuum(self):
        """Optimize database"""
        conn = self._get_conn()
        conn.execute("VACUUM")
        self.logger.info("PERSISTENCE: Database vacuumed")

    def get_db_stats(self) -> Dict:
        """Get database statistics"""
        with self._cursor() as cursor:
            stats = {}

            cursor.execute("SELECT COUNT(*) FROM shadow_whales")
            stats['total_whales'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM trade_history")
            stats['total_trades'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM trade_history WHERE status = 'OPEN'")
            stats['open_positions'] = cursor.fetchone()[0]

            # Database file size
            if os.path.exists(self.db_path):
                stats['db_size_mb'] = os.path.getsize(self.db_path) / (1024 * 1024)

            return stats

    def close(self):
        """Close database connection"""
        if hasattr(self._local, 'conn') and self._local.conn:
            self._local.conn.close()
            self._local.conn = None


# ==================== USAGE EXAMPLE ====================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    db = MimicDB("test_mimic.db")

    # Test whale creation
    whale_id = db.get_or_create_shadow_id("abc123hash", 5000.0)
    print(f"Whale ID: {whale_id}")

    # Test trade logging
    db.log_trade_open(
        trade_id="trade_001",
        shadow_id=whale_id,
        ticker="KXCPI-25DEC-T0.3",
        event_ticker="KXCPI-25DEC",
        side="yes",
        size_usd=100.0,
        contracts=10,
        entry_price=0.45,
        strategy_type="INFORMATIONAL",
        win_prob=0.65
    )

    # Test trade close
    db.log_trade_close("trade_001", exit_price=1.0, pnl=55.0)

    # Update whale stats
    db.update_whale_stats(whale_id, 100.0, True, 55.0, "INFORMATIONAL")

    # Get stats
    print(f"Whale stats: {db.get_whale_stats(whale_id)}")
    print(f"DB stats: {db.get_db_stats()}")

    db.close()
