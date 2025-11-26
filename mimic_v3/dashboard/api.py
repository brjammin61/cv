"""
MIMIC V3.1 Dashboard API
Bloomberg-style real-time monitoring backend

WebSocket streaming for live updates
REST endpoints for historical data
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.requests import Request
from pydantic import BaseModel
import uvicorn

# ═══════════════════════════════════════════════════════════════════════════════
# DATA MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class SystemStatus(str, Enum):
    ONLINE = "ONLINE"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"
    HALTED = "HALTED"

@dataclass
class PortfolioSnapshot:
    """Current portfolio state"""
    timestamp: str
    total_capital: float
    available_capital: float
    deployed_capital: float
    unrealized_pnl: float
    realized_pnl_today: float
    total_pnl_today: float
    pnl_pct_today: float
    open_positions: int
    win_rate_today: float
    trades_today: int

@dataclass
class Position:
    """Active position"""
    ticker: str
    event_title: str
    side: str  # YES/NO
    quantity: int
    avg_entry: float
    current_price: float
    unrealized_pnl: float
    pnl_pct: float
    shadow_id: Optional[str]
    entry_time: str
    hold_time_mins: int

@dataclass
class Trade:
    """Executed trade"""
    trade_id: str
    timestamp: str
    ticker: str
    side: str
    action: str  # OPEN/CLOSE
    quantity: int
    price: float
    pnl: Optional[float]
    shadow_id: Optional[str]
    signal_type: str

@dataclass
class WhaleSignal:
    """Whale activity signal"""
    shadow_id: str
    friendly_name: str
    ticker: str
    side: str
    volume: float
    win_rate: float
    total_pnl: float
    confidence: float
    timestamp: str
    strategy_type: str

@dataclass
class RiskMetrics:
    """Risk management state"""
    current_drawdown_pct: float
    max_drawdown_pct: float
    ddc_multiplier: float
    ddc_status: str  # NORMAL/CAUTIOUS/RESTRICTED/HALTED
    kelly_multiplier: float
    current_exposure_pct: float
    max_exposure_pct: float
    win_streak: int
    loss_streak: int
    var_95: float
    sharpe_ratio: float


@dataclass
class AlphaFeatureSnapshot:
    """Alpha feature engineering state (F.1-F.8)"""
    # Informational Edge (Dankoweb3)
    eis: float              # F.1: Exogenous Info Score
    ers: float              # F.2: Endogeneity Score
    news_latency: float     # F.3: News Latency Delta

    # Structural Edge (bl888m_eth)
    ppd: float              # F.4: Pivot Point Distance
    sres: float             # F.5: S/R Efficacy Score
    mub: float              # F.6: Market Unidirectional Bias

    # Risk Context (Gemchange)
    tii: float              # F.7: Trend Intensity Index
    rrr: float              # F.8: Risk/Reward Ratio

    # Market regime
    market_regime: str
    timestamp: str


@dataclass
class DTFEAnalysis:
    """Digital Twin Foresight Engine analysis result"""
    ticker: str
    title: str
    p_raw: float            # Raw LLM probability
    p_calibrated: float     # Calibrated probability
    tsallis_entropy: float  # F.9: Confidence measure
    optimal_size: float     # F.10: Kelly position size
    reasoning_summary: str  # Chain of thought summary
    key_factors: list       # Driving factors
    risk_flags: list        # Identified risks
    is_tradeable: bool      # Passes entropy threshold
    timestamp: str


@dataclass
class BrainMetrics:
    """ML model performance metrics"""
    accuracy: float
    precision: float
    recall: float
    f1: float
    log_loss: float
    calibration_ece: float  # Expected Calibration Error
    total_predictions: int
    alpha_features_enabled: bool

@dataclass
class MarketMakerStatus:
    """Market maker state"""
    is_active: bool
    active_quotes: int
    markets_quoted: int
    lip_tier: str
    lip_earnings_today: float
    lip_earnings_total: float
    inventory_yes: int
    inventory_no: int
    inventory_skew_active: bool
    avg_spread_bps: float
    fill_rate_pct: float

@dataclass
class SystemHealth:
    """System health metrics"""
    status: str
    uptime_seconds: int
    api_latency_ms: float
    ws_latency_ms: float
    last_heartbeat: str
    errors_1h: int
    warnings_1h: int
    cpu_pct: float
    memory_pct: float
    db_size_mb: float
    rate_limit_remaining: int

@dataclass
class PnLDataPoint:
    """Historical P&L data point"""
    timestamp: str
    cumulative_pnl: float
    realized_pnl: float
    unrealized_pnl: float

# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD STATE MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class DashboardState:
    """
    Central state manager for dashboard data
    Connects to MIMIC engine components
    """

    def __init__(self):
        self.logger = logging.getLogger("Dashboard")
        self._start_time = time.time()

        # Engine component references (set during integration)
        self.risk_manager = None
        self.scanner = None
        self.maker = None
        self.brain = None
        self.db = None
        self.client = None

        # Cached data
        self._portfolio: Optional[PortfolioSnapshot] = None
        self._positions: List[Position] = []
        self._trades: List[Trade] = []
        self._whale_signals: List[WhaleSignal] = []
        self._risk_metrics: Optional[RiskMetrics] = None
        self._maker_status: Optional[MarketMakerStatus] = None
        self._system_health: Optional[SystemHealth] = None
        self._pnl_history: List[PnLDataPoint] = []

        # NEW: Alpha Features and DTFE data
        self._alpha_features: Optional[AlphaFeatureSnapshot] = None
        self._dtfe_analyses: List[DTFEAnalysis] = []
        self._brain_metrics: Optional[BrainMetrics] = None

        # Demo data for standalone testing
        self._demo_mode = True
        self._init_demo_data()

    def _init_demo_data(self):
        """Initialize demo data for standalone testing"""
        now = datetime.utcnow()

        # Portfolio
        self._portfolio = PortfolioSnapshot(
            timestamp=now.isoformat(),
            total_capital=1247.83,
            available_capital=847.83,
            deployed_capital=400.00,
            unrealized_pnl=23.47,
            realized_pnl_today=47.82,
            total_pnl_today=71.29,
            pnl_pct_today=6.05,
            open_positions=4,
            win_rate_today=68.4,
            trades_today=19
        )

        # Positions
        self._positions = [
            Position(
                ticker="KXBTC-25JAN10-T95000",
                event_title="Bitcoin above $95,000?",
                side="YES",
                quantity=45,
                avg_entry=0.67,
                current_price=0.72,
                unrealized_pnl=2.25,
                pnl_pct=7.46,
                shadow_id="Whale_0003",
                entry_time=(now - timedelta(minutes=23)).isoformat(),
                hold_time_mins=23
            ),
            Position(
                ticker="KXINXD-25JAN10-T19500",
                event_title="S&P 500 above 19,500?",
                side="NO",
                quantity=30,
                avg_entry=0.45,
                current_price=0.48,
                unrealized_pnl=-0.90,
                pnl_pct=-6.67,
                shadow_id=None,
                entry_time=(now - timedelta(minutes=45)).isoformat(),
                hold_time_mins=45
            ),
            Position(
                ticker="KXFED-25JAN29-RATECUT",
                event_title="Fed rate cut in January?",
                side="YES",
                quantity=100,
                avg_entry=0.23,
                current_price=0.31,
                unrealized_pnl=8.00,
                pnl_pct=34.78,
                shadow_id="Whale_0001",
                entry_time=(now - timedelta(hours=2)).isoformat(),
                hold_time_mins=120
            ),
            Position(
                ticker="KXNFL-SUPERBOWL-KC",
                event_title="Chiefs win Super Bowl?",
                side="YES",
                quantity=25,
                avg_entry=0.42,
                current_price=0.44,
                unrealized_pnl=0.50,
                pnl_pct=4.76,
                shadow_id="Whale_0007",
                entry_time=(now - timedelta(minutes=8)).isoformat(),
                hold_time_mins=8
            ),
        ]

        # Recent trades
        self._trades = [
            Trade(
                trade_id="T-001928",
                timestamp=(now - timedelta(minutes=2)).isoformat(),
                ticker="KXBTC-25JAN10-T95000",
                side="YES",
                action="OPEN",
                quantity=45,
                price=0.67,
                pnl=None,
                shadow_id="Whale_0003",
                signal_type="WHALE_FOLLOW"
            ),
            Trade(
                trade_id="T-001927",
                timestamp=(now - timedelta(minutes=15)).isoformat(),
                ticker="KXETH-25JAN10-T3500",
                side="NO",
                action="CLOSE",
                quantity=50,
                price=0.62,
                pnl=8.50,
                shadow_id="Whale_0002",
                signal_type="WHALE_FOLLOW"
            ),
            Trade(
                trade_id="T-001926",
                timestamp=(now - timedelta(minutes=28)).isoformat(),
                ticker="KXGOLD-25JAN10-T2700",
                side="YES",
                action="CLOSE",
                quantity=35,
                price=0.81,
                pnl=5.95,
                shadow_id=None,
                signal_type="BRAIN_SIGNAL"
            ),
        ]

        # Whale signals
        self._whale_signals = [
            WhaleSignal(
                shadow_id="WHALE_a3f8b2c1",
                friendly_name="Whale_0001",
                ticker="KXFED-25JAN29-RATECUT",
                side="YES",
                volume=2500.00,
                win_rate=73.2,
                total_pnl=1847.32,
                confidence=0.87,
                timestamp=(now - timedelta(hours=2)).isoformat(),
                strategy_type="MACRO_EVENT"
            ),
            WhaleSignal(
                shadow_id="WHALE_7d2e9f04",
                friendly_name="Whale_0003",
                ticker="KXBTC-25JAN10-T95000",
                side="YES",
                volume=1850.00,
                win_rate=68.7,
                total_pnl=923.18,
                confidence=0.79,
                timestamp=(now - timedelta(minutes=23)).isoformat(),
                strategy_type="CRYPTO_MOMENTUM"
            ),
            WhaleSignal(
                shadow_id="WHALE_1b5c8a92",
                friendly_name="Whale_0007",
                ticker="KXNFL-SUPERBOWL-KC",
                side="YES",
                volume=950.00,
                win_rate=61.3,
                total_pnl=412.55,
                confidence=0.72,
                timestamp=(now - timedelta(minutes=8)).isoformat(),
                strategy_type="SPORTS_SPECIALIST"
            ),
        ]

        # Risk metrics
        self._risk_metrics = RiskMetrics(
            current_drawdown_pct=3.2,
            max_drawdown_pct=8.7,
            ddc_multiplier=0.95,
            ddc_status="NORMAL",
            kelly_multiplier=0.25,
            current_exposure_pct=32.1,
            max_exposure_pct=50.0,
            win_streak=4,
            loss_streak=0,
            var_95=47.50,
            sharpe_ratio=1.83
        )

        # Market maker status
        self._maker_status = MarketMakerStatus(
            is_active=True,
            active_quotes=12,
            markets_quoted=6,
            lip_tier="medium",
            lip_earnings_today=3.47,
            lip_earnings_total=127.83,
            inventory_yes=85,
            inventory_no=42,
            inventory_skew_active=True,
            avg_spread_bps=245,
            fill_rate_pct=23.4
        )

        # System health
        self._system_health = SystemHealth(
            status="ONLINE",
            uptime_seconds=int(time.time() - self._start_time),
            api_latency_ms=45.2,
            ws_latency_ms=12.8,
            last_heartbeat=now.isoformat(),
            errors_1h=0,
            warnings_1h=3,
            cpu_pct=23.4,
            memory_pct=45.7,
            db_size_mb=12.3,
            rate_limit_remaining=892
        )

        # P&L history (last 24 hours, hourly)
        self._pnl_history = []
        cumulative = 1000.0
        for i in range(24):
            ts = now - timedelta(hours=23-i)
            delta = (i - 10) * 2.5 + (i % 3) * 1.5  # Simulated P&L curve
            cumulative += delta
            self._pnl_history.append(PnLDataPoint(
                timestamp=ts.isoformat(),
                cumulative_pnl=cumulative - 1000,
                realized_pnl=delta if delta > 0 else 0,
                unrealized_pnl=delta if delta < 0 else 0
            ))

        # Alpha Features (F.1-F.8) demo data
        self._alpha_features = AlphaFeatureSnapshot(
            eis=0.72,           # F.1: Strong news-driven conviction
            ers=0.35,           # F.2: Low herd behavior (news-driven)
            news_latency=0.85,  # F.3: Good timing advantage
            ppd=0.28,           # F.4: Near S/R level
            sres=0.81,          # F.5: Strong S/R level
            mub=0.67,           # F.6: Bullish bias
            tii=0.73,           # F.7: Trending market
            rrr=0.68,           # F.8: Good risk/reward
            market_regime="TRENDING_UP",
            timestamp=now.isoformat()
        )

        # DTFE Analysis demo data
        self._dtfe_analyses = [
            DTFEAnalysis(
                ticker="KXFED-25JAN29-RATECUT",
                title="Fed Rate Cut in January",
                p_raw=0.72,
                p_calibrated=0.65,
                tsallis_entropy=0.23,
                optimal_size=87.50,
                reasoning_summary="Strong economic indicators suggest Fed will cut rates. Employment data weakening, inflation cooling.",
                key_factors=["Cooling inflation", "Weak jobs data", "Market expectations"],
                risk_flags=["Political uncertainty"],
                is_tradeable=True,
                timestamp=(now - timedelta(minutes=15)).isoformat()
            ),
            DTFEAnalysis(
                ticker="KXBTC-25JAN10-T95000",
                title="Bitcoin above $95,000",
                p_raw=0.58,
                p_calibrated=0.52,
                tsallis_entropy=0.67,
                optimal_size=0.0,
                reasoning_summary="High entropy indicates uncertain LLM prediction. Market sentiment mixed with conflicting signals.",
                key_factors=["ETF inflows", "Regulatory uncertainty"],
                risk_flags=["High entropy", "Volatile asset"],
                is_tradeable=False,
                timestamp=(now - timedelta(minutes=5)).isoformat()
            )
        ]

        # Brain metrics demo data
        self._brain_metrics = BrainMetrics(
            accuracy=0.684,
            precision=0.712,
            recall=0.658,
            f1=0.684,
            log_loss=0.542,
            calibration_ece=0.048,
            total_predictions=1847,
            alpha_features_enabled=True
        )

    def connect_engine(self, risk_manager=None, scanner=None, maker=None,
                       brain=None, db=None, client=None):
        """Connect to MIMIC engine components"""
        self.risk_manager = risk_manager
        self.scanner = scanner
        self.maker = maker
        self.brain = brain
        self.db = db
        self.client = client
        self._demo_mode = False
        self.logger.info("Dashboard connected to MIMIC engine")

    async def refresh_all(self) -> Dict:
        """Refresh all dashboard data"""
        if not self._demo_mode:
            await self._refresh_from_engine()
        else:
            # Update demo timestamps
            self._update_demo_timestamps()

        return self.get_full_state()

    def _update_demo_timestamps(self):
        """Update demo data timestamps for realism"""
        now = datetime.utcnow()
        self._portfolio.timestamp = now.isoformat()
        self._system_health.last_heartbeat = now.isoformat()
        self._system_health.uptime_seconds = int(time.time() - self._start_time)

        # Simulate small price movements
        import random
        for pos in self._positions:
            pos.current_price += random.uniform(-0.01, 0.01)
            pos.current_price = max(0.01, min(0.99, pos.current_price))
            pos.unrealized_pnl = (pos.current_price - pos.avg_entry) * pos.quantity
            pos.pnl_pct = ((pos.current_price / pos.avg_entry) - 1) * 100
            pos.hold_time_mins += 1

    async def _refresh_from_engine(self):
        """Pull live data from engine components"""
        now = datetime.utcnow()

        # Portfolio from risk manager
        if self.risk_manager:
            rm = self.risk_manager
            self._portfolio = PortfolioSnapshot(
                timestamp=now.isoformat(),
                total_capital=rm.current_capital,
                available_capital=rm.current_capital - rm.deployed_capital,
                deployed_capital=rm.deployed_capital,
                unrealized_pnl=sum(p.get('unrealized_pnl', 0) for p in rm.open_positions.values()),
                realized_pnl_today=rm.realized_pnl_today,
                total_pnl_today=rm.realized_pnl_today + sum(p.get('unrealized_pnl', 0) for p in rm.open_positions.values()),
                pnl_pct_today=((rm.current_capital / rm.initial_capital) - 1) * 100,
                open_positions=len(rm.open_positions),
                win_rate_today=rm.win_rate if hasattr(rm, 'win_rate') else 0,
                trades_today=rm.trades_today if hasattr(rm, 'trades_today') else 0
            )

            # Risk metrics
            self._risk_metrics = RiskMetrics(
                current_drawdown_pct=rm.current_drawdown * 100,
                max_drawdown_pct=rm.max_drawdown * 100,
                ddc_multiplier=rm.ddc_multiplier,
                ddc_status=rm.ddc_status if hasattr(rm, 'ddc_status') else "NORMAL",
                kelly_multiplier=rm.kelly_fraction,
                current_exposure_pct=(rm.deployed_capital / rm.current_capital) * 100,
                max_exposure_pct=rm.max_portfolio_exposure * 100,
                win_streak=rm.win_streak if hasattr(rm, 'win_streak') else 0,
                loss_streak=rm.loss_streak if hasattr(rm, 'loss_streak') else 0,
                var_95=rm.var_95 if hasattr(rm, 'var_95') else 0,
                sharpe_ratio=rm.sharpe_ratio if hasattr(rm, 'sharpe_ratio') else 0
            )

        # Whale signals from scanner
        if self.scanner:
            self._whale_signals = []
            for shadow_id, data in self.scanner.shadow_profiles.items():
                if data.get('volume', 0) > self.scanner.volume_threshold:
                    self._whale_signals.append(WhaleSignal(
                        shadow_id=shadow_id,
                        friendly_name=data.get('friendly_id', shadow_id[:12]),
                        ticker=data.get('last_ticker', ''),
                        side=data.get('last_side', ''),
                        volume=data.get('volume', 0),
                        win_rate=data.get('win_rate', 0) * 100,
                        total_pnl=data.get('total_pnl', 0),
                        confidence=data.get('confidence', 0),
                        timestamp=data.get('last_seen', now.isoformat()),
                        strategy_type=data.get('strategy_type', 'UNKNOWN')
                    ))

        # Market maker status
        if self.maker:
            self._maker_status = MarketMakerStatus(
                is_active=self.maker.is_active,
                active_quotes=len(self.maker.active_orders),
                markets_quoted=len(self.maker.quoted_markets),
                lip_tier=self.maker.current_lip_tier,
                lip_earnings_today=self.maker.lip_earnings_today,
                lip_earnings_total=self.maker.lip_earnings_total,
                inventory_yes=sum(1 for p in self.maker.inventory.values() if p > 0),
                inventory_no=sum(1 for p in self.maker.inventory.values() if p < 0),
                inventory_skew_active=self.maker.inventory_skew_active,
                avg_spread_bps=self.maker.avg_spread_bps,
                fill_rate_pct=self.maker.fill_rate * 100
            )

    def get_full_state(self) -> Dict:
        """Get complete dashboard state"""
        return {
            "portfolio": asdict(self._portfolio) if self._portfolio else None,
            "positions": [asdict(p) for p in self._positions],
            "trades": [asdict(t) for t in self._trades[-50:]],  # Last 50 trades
            "whale_signals": [asdict(w) for w in self._whale_signals],
            "risk_metrics": asdict(self._risk_metrics) if self._risk_metrics else None,
            "maker_status": asdict(self._maker_status) if self._maker_status else None,
            "system_health": asdict(self._system_health) if self._system_health else None,
            "pnl_history": [asdict(p) for p in self._pnl_history],
            # NEW: Alpha Features and DTFE
            "alpha_features": asdict(self._alpha_features) if self._alpha_features else None,
            "dtfe_analyses": [asdict(d) for d in self._dtfe_analyses],
            "brain_metrics": asdict(self._brain_metrics) if self._brain_metrics else None,
            "server_time": datetime.utcnow().isoformat(),
            "demo_mode": self._demo_mode
        }

    def get_portfolio(self) -> Dict:
        return asdict(self._portfolio) if self._portfolio else {}

    def get_positions(self) -> List[Dict]:
        return [asdict(p) for p in self._positions]

    def get_trades(self, limit: int = 50) -> List[Dict]:
        return [asdict(t) for t in self._trades[-limit:]]

    def get_whale_signals(self) -> List[Dict]:
        return [asdict(w) for w in self._whale_signals]

    def get_risk_metrics(self) -> Dict:
        return asdict(self._risk_metrics) if self._risk_metrics else {}

    def get_maker_status(self) -> Dict:
        return asdict(self._maker_status) if self._maker_status else {}

    def get_system_health(self) -> Dict:
        return asdict(self._system_health) if self._system_health else {}

    def get_pnl_history(self) -> List[Dict]:
        return [asdict(p) for p in self._pnl_history]

    def get_alpha_features(self) -> Dict:
        """Get current alpha feature state"""
        if not self._demo_mode and self.brain is not None:
            # Pull from brain's alpha extractor
            try:
                if hasattr(self.brain, 'alpha_extractor') and self.brain.alpha_extractor is not None:
                    features = self.brain.alpha_extractor.extract_features(
                        current_price=0.5,  # Default
                        win_prob=0.5
                    )
                    self._alpha_features = AlphaFeatureSnapshot(
                        eis=features.exogenous_info_score,
                        ers=features.endogeneity_score,
                        news_latency=features.news_latency_delta,
                        ppd=features.pivot_point_distance,
                        sres=features.sr_efficacy_score,
                        mub=features.market_unidirectional_bias,
                        tii=features.trend_intensity_index,
                        rrr=features.risk_reward_ratio,
                        market_regime=features.market_regime,
                        timestamp=datetime.utcnow().isoformat()
                    )
            except Exception as e:
                self.logger.error(f"Error getting alpha features: {e}")

        return asdict(self._alpha_features) if self._alpha_features else {}

    def get_dtfe_analyses(self) -> List[Dict]:
        """Get DTFE analysis results"""
        return [asdict(d) for d in self._dtfe_analyses]

    def get_brain_metrics(self) -> Dict:
        """Get brain/ML metrics"""
        if not self._demo_mode and self.brain is not None:
            try:
                metrics = self.brain.get_metrics()
                self._brain_metrics = BrainMetrics(
                    accuracy=metrics.get('accuracy', 0),
                    precision=metrics.get('precision', 0),
                    recall=metrics.get('recall', 0),
                    f1=metrics.get('f1', 0),
                    log_loss=metrics.get('log_loss', 0),
                    calibration_ece=metrics.get('calibration', {}).get('avg_adjustment', 0),
                    total_predictions=len(self.brain.predictions) if hasattr(self.brain, 'predictions') else 0,
                    alpha_features_enabled=hasattr(self.brain, 'alpha_extractor') and self.brain.alpha_extractor is not None
                )
            except Exception as e:
                self.logger.error(f"Error getting brain metrics: {e}")

        return asdict(self._brain_metrics) if self._brain_metrics else {}


# ═══════════════════════════════════════════════════════════════════════════════
# WEBSOCKET CONNECTION MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class ConnectionManager:
    """Manage WebSocket connections for real-time updates"""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.logger = logging.getLogger("WSManager")

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        self.logger.info(f"Client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        self.logger.info(f"Client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: Dict):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            return

        data = json.dumps(message)
        disconnected = set()

        for connection in self.active_connections:
            try:
                await connection.send_text(data)
            except Exception:
                disconnected.add(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.active_connections.discard(conn)

    async def send_personal(self, websocket: WebSocket, message: Dict):
        """Send message to specific client"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception:
            self.active_connections.discard(websocket)


# ═══════════════════════════════════════════════════════════════════════════════
# FASTAPI APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════

# Initialize app
app = FastAPI(
    title="MIMIC V3.1 Dashboard",
    description="Bloomberg-style trading system monitor",
    version="3.1.0"
)

# State and connections
dashboard_state = DashboardState()
ws_manager = ConnectionManager()

# Mount static files and templates
import os
DASHBOARD_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(DASHBOARD_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(DASHBOARD_DIR, "templates"))

# ─────────────────────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Serve main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "title": "MIMIC V3.1 Terminal"
    })

@app.get("/api/state")
async def get_full_state():
    """Get complete dashboard state"""
    return await dashboard_state.refresh_all()

@app.get("/api/portfolio")
async def get_portfolio():
    """Get portfolio snapshot"""
    return dashboard_state.get_portfolio()

@app.get("/api/positions")
async def get_positions():
    """Get active positions"""
    return dashboard_state.get_positions()

@app.get("/api/trades")
async def get_trades(limit: int = 50):
    """Get recent trades"""
    return dashboard_state.get_trades(limit)

@app.get("/api/whales")
async def get_whale_signals():
    """Get whale signals"""
    return dashboard_state.get_whale_signals()

@app.get("/api/risk")
async def get_risk_metrics():
    """Get risk metrics"""
    return dashboard_state.get_risk_metrics()

@app.get("/api/maker")
async def get_maker_status():
    """Get market maker status"""
    return dashboard_state.get_maker_status()

@app.get("/api/health")
async def get_system_health():
    """Get system health"""
    return dashboard_state.get_system_health()

@app.get("/api/pnl-history")
async def get_pnl_history():
    """Get P&L history"""
    return dashboard_state.get_pnl_history()


@app.get("/api/alpha-features")
async def get_alpha_features():
    """Get current alpha feature state (F.1-F.8)"""
    return dashboard_state.get_alpha_features()


@app.get("/api/dtfe")
async def get_dtfe_analyses():
    """Get DTFE analysis results"""
    return dashboard_state.get_dtfe_analyses()


@app.get("/api/brain")
async def get_brain_metrics():
    """Get ML/Brain performance metrics"""
    return dashboard_state.get_brain_metrics()


# ─────────────────────────────────────────────────────────────────────────────
# WEBSOCKET
# ─────────────────────────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await ws_manager.connect(websocket)

    try:
        # Send initial state
        state = await dashboard_state.refresh_all()
        await ws_manager.send_personal(websocket, {
            "type": "INITIAL_STATE",
            "data": state
        })

        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for client messages (ping/pong, commands)
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )

                msg = json.loads(data)

                if msg.get("type") == "PING":
                    await ws_manager.send_personal(websocket, {"type": "PONG"})

                elif msg.get("type") == "REFRESH":
                    state = await dashboard_state.refresh_all()
                    await ws_manager.send_personal(websocket, {
                        "type": "STATE_UPDATE",
                        "data": state
                    })

            except asyncio.TimeoutError:
                # Send heartbeat
                await ws_manager.send_personal(websocket, {"type": "HEARTBEAT"})

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)


# ─────────────────────────────────────────────────────────────────────────────
# BACKGROUND TASKS
# ─────────────────────────────────────────────────────────────────────────────

async def broadcast_updates():
    """Periodically broadcast state updates to all clients"""
    while True:
        await asyncio.sleep(1.0)  # 1 second update interval

        if ws_manager.active_connections:
            state = await dashboard_state.refresh_all()
            await ws_manager.broadcast({
                "type": "STATE_UPDATE",
                "data": state
            })

@app.on_event("startup")
async def startup_event():
    """Start background tasks on app startup"""
    asyncio.create_task(broadcast_updates())
    logging.info("MIMIC Dashboard started")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logging.info("MIMIC Dashboard stopping")


# ═══════════════════════════════════════════════════════════════════════════════
# STANDALONE RUNNER
# ═══════════════════════════════════════════════════════════════════════════════

def run_dashboard(host: str = "0.0.0.0", port: int = 8080):
    """Run dashboard server standalone"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
    )

    print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         MIMIC V3.1 DASHBOARD                                  ║
║                     Bloomberg-Style Trading Monitor                           ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Server starting on http://{host}:{port}                                      ║
║  Open in browser to view dashboard                                           ║
║  Press Ctrl+C to stop                                                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    run_dashboard()
