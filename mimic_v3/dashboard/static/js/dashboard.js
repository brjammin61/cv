/**
 * MIMIC V3.1 Dashboard - Real-time Terminal Interface
 * WebSocket-powered Bloomberg-style trading monitor
 */

// ═══════════════════════════════════════════════════════════════════════════════
// CONFIGURATION
// ═══════════════════════════════════════════════════════════════════════════════

const CONFIG = {
    WS_RECONNECT_DELAY: 2000,
    WS_MAX_RETRIES: 10,
    UPDATE_INTERVAL: 1000,
    CHART_MAX_POINTS: 100,
    ANIMATION_DURATION: 300,
};

// ═══════════════════════════════════════════════════════════════════════════════
// STATE MANAGEMENT
// ═══════════════════════════════════════════════════════════════════════════════

class DashboardState {
    constructor() {
        this.portfolio = null;
        this.positions = [];
        this.trades = [];
        this.whaleSignals = [];
        this.riskMetrics = null;
        this.makerStatus = null;
        this.systemHealth = null;
        this.pnlHistory = [];
        this.isConnected = false;
        this.isDemoMode = false;
        this.lastUpdate = null;
    }

    update(data) {
        if (data.portfolio) this.portfolio = data.portfolio;
        if (data.positions) this.positions = data.positions;
        if (data.trades) this.trades = data.trades;
        if (data.whale_signals) this.whaleSignals = data.whale_signals;
        if (data.risk_metrics) this.riskMetrics = data.risk_metrics;
        if (data.maker_status) this.makerStatus = data.maker_status;
        if (data.system_health) this.systemHealth = data.system_health;
        if (data.pnl_history) this.pnlHistory = data.pnl_history;
        if (data.demo_mode !== undefined) this.isDemoMode = data.demo_mode;
        this.lastUpdate = new Date();
    }
}

const state = new DashboardState();

// ═══════════════════════════════════════════════════════════════════════════════
// WEBSOCKET MANAGER
// ═══════════════════════════════════════════════════════════════════════════════

class WebSocketManager {
    constructor() {
        this.ws = null;
        this.retryCount = 0;
        this.pingInterval = null;
    }

    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;

        console.log('[WS] Connecting to', wsUrl);
        this.updateStatus('connecting');

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log('[WS] Connected');
            this.retryCount = 0;
            state.isConnected = true;
            this.updateStatus('online');
            this.startPing();
        };

        this.ws.onclose = (event) => {
            console.log('[WS] Disconnected', event.code);
            state.isConnected = false;
            this.updateStatus('offline');
            this.stopPing();
            this.scheduleReconnect();
        };

        this.ws.onerror = (error) => {
            console.error('[WS] Error', error);
            this.updateStatus('offline');
        };

        this.ws.onmessage = (event) => {
            try {
                const msg = JSON.parse(event.data);
                this.handleMessage(msg);
            } catch (e) {
                console.error('[WS] Parse error', e);
            }
        };
    }

    handleMessage(msg) {
        switch (msg.type) {
            case 'INITIAL_STATE':
            case 'STATE_UPDATE':
                state.update(msg.data);
                renderAll();
                break;
            case 'HEARTBEAT':
                // Connection alive
                break;
            case 'PONG':
                // Ping response
                break;
            default:
                console.log('[WS] Unknown message type:', msg.type);
        }
    }

    send(msg) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(msg));
        }
    }

    startPing() {
        this.pingInterval = setInterval(() => {
            this.send({ type: 'PING' });
        }, 30000);
    }

    stopPing() {
        if (this.pingInterval) {
            clearInterval(this.pingInterval);
            this.pingInterval = null;
        }
    }

    scheduleReconnect() {
        if (this.retryCount < CONFIG.WS_MAX_RETRIES) {
            this.retryCount++;
            const delay = CONFIG.WS_RECONNECT_DELAY * Math.pow(2, this.retryCount - 1);
            console.log(`[WS] Reconnecting in ${delay}ms (attempt ${this.retryCount})`);
            setTimeout(() => this.connect(), delay);
        } else {
            console.error('[WS] Max retries exceeded');
            this.updateStatus('offline');
        }
    }

    updateStatus(status) {
        const dot = document.getElementById('status-dot');
        const text = document.getElementById('status-text');

        dot.className = 'status-dot ' + status;

        switch (status) {
            case 'online':
                text.textContent = 'ONLINE';
                text.style.color = '#00ff88';
                break;
            case 'connecting':
                text.textContent = 'CONNECTING';
                text.style.color = '#ffcc00';
                break;
            case 'offline':
                text.textContent = 'OFFLINE';
                text.style.color = '#ff4444';
                break;
            case 'halted':
                text.textContent = 'HALTED';
                text.style.color = '#ff4444';
                break;
        }
    }

    refresh() {
        this.send({ type: 'REFRESH' });
    }
}

const wsManager = new WebSocketManager();

// ═══════════════════════════════════════════════════════════════════════════════
// CHART MANAGER
// ═══════════════════════════════════════════════════════════════════════════════

class ChartManager {
    constructor() {
        this.pnlChart = null;
    }

    initPnLChart() {
        const ctx = document.getElementById('pnl-chart').getContext('2d');

        this.pnlChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Cumulative P&L',
                    data: [],
                    borderColor: '#ff8c00',
                    backgroundColor: 'rgba(255, 140, 0, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index',
                },
                plugins: {
                    legend: {
                        display: false,
                    },
                    tooltip: {
                        backgroundColor: '#1a1a1a',
                        titleColor: '#ffffff',
                        bodyColor: '#b0b0b0',
                        borderColor: '#333333',
                        borderWidth: 1,
                        padding: 10,
                        displayColors: false,
                        callbacks: {
                            label: (context) => `P&L: $${context.parsed.y.toFixed(2)}`,
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        grid: {
                            color: '#222222',
                            drawBorder: false,
                        },
                        ticks: {
                            color: '#666666',
                            font: { size: 9 },
                            maxRotation: 0,
                            maxTicksLimit: 6,
                        }
                    },
                    y: {
                        display: true,
                        grid: {
                            color: '#222222',
                            drawBorder: false,
                        },
                        ticks: {
                            color: '#666666',
                            font: { size: 9 },
                            callback: (value) => '$' + value.toFixed(0),
                        }
                    }
                },
                animation: {
                    duration: CONFIG.ANIMATION_DURATION,
                }
            }
        });
    }

    updatePnLChart(history) {
        if (!this.pnlChart || !history || history.length === 0) return;

        const labels = history.map(p => {
            const date = new Date(p.timestamp);
            return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
        });

        const data = history.map(p => p.cumulative_pnl);

        // Update chart data
        this.pnlChart.data.labels = labels;
        this.pnlChart.data.datasets[0].data = data;

        // Color based on P&L
        const lastValue = data[data.length - 1] || 0;
        if (lastValue >= 0) {
            this.pnlChart.data.datasets[0].borderColor = '#00ff88';
            this.pnlChart.data.datasets[0].backgroundColor = 'rgba(0, 255, 136, 0.1)';
        } else {
            this.pnlChart.data.datasets[0].borderColor = '#ff4444';
            this.pnlChart.data.datasets[0].backgroundColor = 'rgba(255, 68, 68, 0.1)';
        }

        this.pnlChart.update('none');
    }
}

const chartManager = new ChartManager();

// ═══════════════════════════════════════════════════════════════════════════════
// FORMATTERS
// ═══════════════════════════════════════════════════════════════════════════════

const formatters = {
    currency(value, decimals = 2) {
        if (value === null || value === undefined) return '$0.00';
        const sign = value >= 0 ? '' : '-';
        return `${sign}$${Math.abs(value).toFixed(decimals)}`;
    },

    currencyWithSign(value, decimals = 2) {
        if (value === null || value === undefined) return '$0.00';
        const sign = value >= 0 ? '+' : '';
        return `${sign}$${value.toFixed(decimals)}`;
    },

    percent(value, decimals = 1) {
        if (value === null || value === undefined) return '0%';
        const sign = value >= 0 ? '+' : '';
        return `${sign}${value.toFixed(decimals)}%`;
    },

    percentNoSign(value, decimals = 1) {
        if (value === null || value === undefined) return '0%';
        return `${value.toFixed(decimals)}%`;
    },

    number(value, decimals = 0) {
        if (value === null || value === undefined) return '0';
        return value.toFixed(decimals);
    },

    time(isoString) {
        if (!isoString) return '--:--';
        const date = new Date(isoString);
        return date.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        });
    },

    duration(seconds) {
        if (!seconds || seconds < 0) return '0s';
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        const s = Math.floor(seconds % 60);

        if (h > 0) return `${h}h ${m}m`;
        if (m > 0) return `${m}m ${s}s`;
        return `${s}s`;
    },

    ticker(ticker) {
        if (!ticker) return '';
        // Truncate long tickers
        return ticker.length > 20 ? ticker.substring(0, 17) + '...' : ticker;
    },

    pnlClass(value) {
        if (value > 0) return 'pnl-positive text-positive';
        if (value < 0) return 'pnl-negative text-negative';
        return '';
    },

    sideClass(side) {
        return side === 'YES' ? 'side-yes text-positive' : 'side-no text-negative';
    }
};

// ═══════════════════════════════════════════════════════════════════════════════
// RENDER FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════════

function renderAll() {
    renderHeader();
    renderPortfolio();
    renderPositions();
    renderTrades();
    renderWhales();
    renderRisk();
    renderMaker();
    renderFooter();
    chartManager.updatePnLChart(state.pnlHistory);
}

function renderHeader() {
    const p = state.portfolio;
    if (!p) return;

    // Capital
    document.getElementById('header-capital').textContent = formatters.currency(p.total_capital);

    // P&L with color
    const pnlEl = document.getElementById('header-pnl');
    pnlEl.textContent = formatters.currencyWithSign(p.total_pnl_today);
    pnlEl.className = 'header-stat-value ' + (p.total_pnl_today >= 0 ? 'positive' : 'negative');

    // Win rate with color
    const wrEl = document.getElementById('header-winrate');
    wrEl.textContent = formatters.percentNoSign(p.win_rate_today);
    wrEl.className = 'header-stat-value ' + (p.win_rate_today >= 50 ? 'positive' : 'negative');

    // Positions
    document.getElementById('header-positions').textContent = p.open_positions;

    // Update time
    updateClock();
}

function renderPortfolio() {
    const p = state.portfolio;
    if (!p) return;

    // Main metrics
    document.getElementById('portfolio-capital').textContent = formatters.currency(p.total_capital);
    document.getElementById('portfolio-available').textContent = formatters.currency(p.available_capital);
    document.getElementById('portfolio-deployed').textContent = formatters.currency(p.deployed_capital);

    // Unrealized P&L
    const unrealizedEl = document.getElementById('portfolio-unrealized');
    unrealizedEl.textContent = formatters.currencyWithSign(p.unrealized_pnl);
    unrealizedEl.className = 'portfolio-metric-value ' + (p.unrealized_pnl >= 0 ? 'text-positive' : 'text-negative');

    // Realized P&L
    const realizedEl = document.getElementById('portfolio-realized');
    realizedEl.textContent = formatters.currencyWithSign(p.realized_pnl_today);
    realizedEl.className = 'portfolio-metric-value ' + (p.realized_pnl_today >= 0 ? 'text-positive' : 'text-negative');

    // Percent
    const pctEl = document.getElementById('portfolio-pct');
    pctEl.textContent = formatters.percent(p.pnl_pct_today);
    pctEl.className = 'portfolio-metric-value ' + (p.pnl_pct_today >= 0 ? 'text-positive' : 'text-negative');
}

function renderPositions() {
    const positions = state.positions || [];
    document.getElementById('positions-count').textContent = positions.length;

    const tbody = document.getElementById('positions-table');
    tbody.innerHTML = positions.map(pos => `
        <tr>
            <td class="ticker" title="${pos.ticker}">${formatters.ticker(pos.ticker)}</td>
            <td class="${formatters.sideClass(pos.side)}">${pos.side}</td>
            <td>${pos.quantity}</td>
            <td>${pos.avg_entry.toFixed(2)}</td>
            <td>${pos.current_price.toFixed(2)}</td>
            <td class="${formatters.pnlClass(pos.unrealized_pnl)}">
                ${formatters.currencyWithSign(pos.unrealized_pnl)}
                <span style="opacity: 0.6; font-size: 9px;">(${formatters.percent(pos.pnl_pct)})</span>
            </td>
            <td>${pos.shadow_id ? `<span class="whale-badge">${pos.shadow_id}</span>` : '-'}</td>
        </tr>
    `).join('');
}

function renderTrades() {
    const trades = state.trades || [];
    const p = state.portfolio;
    document.getElementById('trades-count').textContent = p ? `${p.trades_today} today` : '0 today';

    const tbody = document.getElementById('trades-table');
    tbody.innerHTML = trades.slice().reverse().map(trade => {
        const signalClass = trade.signal_type.includes('WHALE') ? 'whale' :
                           trade.signal_type.includes('BRAIN') ? 'brain' : 'maker';
        return `
            <tr class="trade-row-${trade.action.toLowerCase()}">
                <td>${formatters.time(trade.timestamp)}</td>
                <td class="ticker" title="${trade.ticker}">${formatters.ticker(trade.ticker)}</td>
                <td><span class="trade-action ${trade.action.toLowerCase()}">${trade.action}</span></td>
                <td class="${formatters.sideClass(trade.side)}">${trade.side}</td>
                <td>${trade.quantity}</td>
                <td>${trade.price.toFixed(2)}</td>
                <td class="${trade.pnl !== null ? formatters.pnlClass(trade.pnl) : ''}">
                    ${trade.pnl !== null ? formatters.currencyWithSign(trade.pnl) : '-'}
                </td>
                <td><span class="signal-badge ${signalClass}">${trade.signal_type.replace('_', ' ')}</span></td>
            </tr>
        `;
    }).join('');
}

function renderWhales() {
    const whales = state.whaleSignals || [];
    document.getElementById('whales-count').textContent = whales.length;

    const container = document.getElementById('whale-list');
    container.innerHTML = whales.map(whale => {
        const confClass = whale.confidence >= 0.75 ? 'high' :
                         whale.confidence >= 0.5 ? 'medium' : 'low';
        return `
            <div class="whale-card fade-in">
                <div class="whale-card-header">
                    <span class="whale-name">${whale.friendly_name}</span>
                    <span class="whale-confidence ${confClass}">${(whale.confidence * 100).toFixed(0)}%</span>
                </div>
                <div class="whale-signal">
                    <span class="${formatters.sideClass(whale.side)}">${whale.side}</span>
                    ${formatters.ticker(whale.ticker)}
                </div>
                <div class="whale-stats">
                    <span>Vol: <span class="whale-stat-value">${formatters.currency(whale.volume, 0)}</span></span>
                    <span>WR: <span class="whale-stat-value ${whale.win_rate >= 50 ? 'text-positive' : 'text-negative'}">${formatters.percentNoSign(whale.win_rate)}</span></span>
                    <span>P&L: <span class="whale-stat-value ${formatters.pnlClass(whale.total_pnl)}">${formatters.currency(whale.total_pnl)}</span></span>
                </div>
            </div>
        `;
    }).join('');
}

function renderRisk() {
    const r = state.riskMetrics;
    if (!r) return;

    // Drawdown
    const ddEl = document.getElementById('risk-drawdown');
    ddEl.textContent = formatters.percentNoSign(r.current_drawdown_pct);
    ddEl.className = 'risk-gauge-value ' + (r.current_drawdown_pct > 15 ? 'text-negative' : r.current_drawdown_pct > 10 ? 'text-warning' : 'text-positive');

    const ddBar = document.getElementById('risk-drawdown-bar');
    ddBar.style.width = `${Math.min(r.current_drawdown_pct / 25 * 100, 100)}%`;
    ddBar.className = 'risk-gauge-fill ' + (r.current_drawdown_pct > 15 ? 'danger' : r.current_drawdown_pct > 10 ? 'caution' : 'safe');

    // Exposure
    const expEl = document.getElementById('risk-exposure');
    expEl.textContent = formatters.percentNoSign(r.current_exposure_pct);

    const expBar = document.getElementById('risk-exposure-bar');
    expBar.style.width = `${Math.min(r.current_exposure_pct / r.max_exposure_pct * 100, 100)}%`;
    expBar.className = 'risk-gauge-fill ' + (r.current_exposure_pct > 40 ? 'caution' : 'safe');

    // DDC Multiplier
    document.getElementById('risk-ddc-mult').textContent = r.ddc_multiplier.toFixed(2);
    const ddcBar = document.getElementById('risk-ddc-bar');
    ddcBar.style.width = `${r.ddc_multiplier * 100}%`;
    ddcBar.className = 'risk-gauge-fill ' + (r.ddc_multiplier < 0.5 ? 'danger' : r.ddc_multiplier < 0.8 ? 'caution' : 'safe');

    // Kelly
    document.getElementById('risk-kelly').textContent = r.kelly_multiplier.toFixed(2);
    const kellyBar = document.getElementById('risk-kelly-bar');
    kellyBar.style.width = `${r.kelly_multiplier * 100}%`;

    // Streaks
    document.getElementById('risk-win-streak').textContent = r.win_streak;
    document.getElementById('risk-loss-streak').textContent = r.loss_streak;

    // DDC Status Badge
    const ddcBadge = document.getElementById('ddc-badge');
    ddcBadge.textContent = r.ddc_status;
    ddcBadge.className = 'ddc-badge ' + r.ddc_status.toLowerCase();

    const statusBadge = document.getElementById('ddc-status-badge');
    statusBadge.textContent = r.ddc_status;
    statusBadge.className = 'panel-badge ' + (r.ddc_status === 'NORMAL' ? 'live' : '');
}

function renderMaker() {
    const m = state.makerStatus;
    if (!m) return;

    // Status badge
    const statusBadge = document.getElementById('maker-status-badge');
    statusBadge.textContent = m.is_active ? 'ACTIVE' : 'INACTIVE';
    statusBadge.className = 'panel-badge ' + (m.is_active ? 'live' : '');

    // Stats
    document.getElementById('maker-quotes').textContent = m.active_quotes;
    document.getElementById('maker-markets').textContent = m.markets_quoted;

    // LIP Tier
    const lipTier = document.getElementById('maker-lip-tier');
    lipTier.textContent = m.lip_tier.toUpperCase();
    lipTier.className = 'lip-tier-badge ' + m.lip_tier;

    // LIP Today
    document.getElementById('maker-lip-today').textContent = formatters.currency(m.lip_earnings_today);

    // Spread & Fill Rate
    document.getElementById('maker-spread').textContent = `${m.avg_spread_bps} bps`;
    document.getElementById('maker-fill-rate').textContent = formatters.percentNoSign(m.fill_rate_pct);

    // Inventory bar
    const totalInv = m.inventory_yes + m.inventory_no;
    const yesWidth = totalInv > 0 ? (m.inventory_yes / totalInv) * 100 : 50;
    const noWidth = totalInv > 0 ? (m.inventory_no / totalInv) * 100 : 50;

    const yesBar = document.getElementById('inventory-yes');
    yesBar.style.width = `${yesWidth}%`;
    yesBar.textContent = `YES: ${m.inventory_yes}`;

    const noBar = document.getElementById('inventory-no');
    noBar.style.width = `${noWidth}%`;
    noBar.textContent = `NO: ${m.inventory_no}`;
}

function renderFooter() {
    const h = state.systemHealth;
    if (!h) return;

    // API Latency
    const apiLatency = document.getElementById('footer-api-latency');
    apiLatency.textContent = `${h.api_latency_ms.toFixed(0)}ms`;
    apiLatency.className = 'footer-stat-value ' + (h.api_latency_ms > 200 ? 'bad' : h.api_latency_ms > 100 ? 'warn' : 'good');

    // WS Latency
    const wsLatency = document.getElementById('footer-ws-latency');
    wsLatency.textContent = `${h.ws_latency_ms.toFixed(0)}ms`;
    wsLatency.className = 'footer-stat-value ' + (h.ws_latency_ms > 50 ? 'warn' : 'good');

    // Uptime
    document.getElementById('footer-uptime').textContent = formatters.duration(h.uptime_seconds);

    // Errors
    const errorsEl = document.getElementById('footer-errors');
    errorsEl.textContent = h.errors_1h;
    errorsEl.className = 'footer-stat-value ' + (h.errors_1h > 0 ? 'bad' : 'good');

    // Rate Limit
    const rlEl = document.getElementById('footer-rate-limit');
    rlEl.textContent = h.rate_limit_remaining;
    rlEl.className = 'footer-stat-value ' + (h.rate_limit_remaining < 100 ? 'warn' : 'good');

    // DB Size
    document.getElementById('footer-db-size').textContent = `DB: ${h.db_size_mb.toFixed(1)}MB`;

    // Demo Mode badge
    const demoBadge = document.getElementById('demo-badge');
    demoBadge.style.display = state.isDemoMode ? 'block' : 'none';
}

function updateClock() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false,
        timeZone: 'UTC'
    });
    document.getElementById('header-time').textContent = timeStr;
}

// ═══════════════════════════════════════════════════════════════════════════════
// INITIALIZATION
// ═══════════════════════════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
    console.log('[Dashboard] Initializing MIMIC V3.1 Terminal');

    // Initialize chart
    chartManager.initPnLChart();

    // Connect WebSocket
    wsManager.connect();

    // Start clock update
    setInterval(updateClock, 1000);
    updateClock();

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.key === 'r' && (e.ctrlKey || e.metaKey)) {
            e.preventDefault();
            wsManager.refresh();
        }
    });

    console.log('[Dashboard] Ready');
});

// ═══════════════════════════════════════════════════════════════════════════════
// EXPORTS (for console debugging)
// ═══════════════════════════════════════════════════════════════════════════════

window.mimicDashboard = {
    state,
    wsManager,
    chartManager,
    refresh: () => wsManager.refresh(),
};
