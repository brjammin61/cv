# MIMIC V3.1 Technical Specification
## Comprehensive System Breakdown for Research Review

**Version:** 3.1.0
**Date:** November 25, 2025
**Status:** Ready for Review

---

# Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture Deep Dive](#2-architecture-deep-dive)
3. [Module Specifications](#3-module-specifications)
   - 3.1 [Kalshi Client](#31-kalshi-client)
   - 3.2 [Context Parser](#32-context-parser)
   - 3.3 [Shadow Scanner](#33-shadow-scanner)
   - 3.4 [Mimic Brain](#34-mimic-brain)
   - 3.5 [Risk Engine](#35-risk-engine)
   - 3.6 [News Oracle](#36-news-oracle)
   - 3.7 [Market Maker](#37-market-maker)
   - 3.8 [Central Cortex](#38-central-cortex)
4. [Data Flows](#4-data-flows)
5. [Algorithms & Formulas](#5-algorithms--formulas)
6. [Known Limitations](#6-known-limitations)
7. [Potential Improvements](#7-potential-improvements)
8. [Research Questions](#8-research-questions)

---

# 1. System Overview

## 1.1 Purpose

MIMIC V3.1 is a high-frequency trading system designed for Kalshi prediction markets. It operates on two parallel strategies:

1. **Taker Strategy (Alpha Generation)**: Detect and follow "whale" traders who demonstrate edge, validated by news sentiment analysis
2. **Maker Strategy (Structural Alpha)**: Capture liquidity rebates and exploit Favorite-Longshot Bias through passive market making

## 1.2 Core Hypothesis

The system is built on several market microstructure hypotheses:

| Hypothesis | Basis | Implementation |
|------------|-------|----------------|
| Whale Edge Exists | Large traders on Kalshi have informational advantages | Shadow ID tracking + win rate analysis |
| Resolution Arbitrage | Near-settlement trades at extreme prices indicate known outcomes | Resolution proximity detection |
| Favorite-Longshot Bias | Markets overprice longshots, underprice favorites | Maker quotes on favorite side |
| News Leads Price | Sentiment shifts precede market moves | Perplexity API news analysis |
| Online Learning Adapts | Market regimes change; batch models go stale | River incremental learning |

## 1.3 Execution Philosophy

```
SPEED HIERARCHY:
1. Resolution Arb (FAST LANE) → Skip Oracle → Direct execution
2. Informational Whale (SLOW LANE) → Oracle validation → ML prediction → Execution
3. No Signal → Maker farming (background)
```

---

# 2. Architecture Deep Dive

## 2.1 System Diagram

```
┌────────────────────────────────────────────────────────────────────────────┐
│                              MIMIC CORTEX                                   │
│                         (Async Event Loop Orchestrator)                     │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐ │
│  │   SCANNER   │───▶│   ORACLE    │───▶│    BRAIN    │───▶│    RISK     │ │
│  │             │    │             │    │             │    │   ENGINE    │ │
│  │ - Whale ID  │    │ - Perplexity│    │ - River ML  │    │             │ │
│  │ - Volume    │    │ - Sentiment │    │ - Features  │    │ - Asym Kelly│ │
│  │ - Resolution│    │ - Caching   │    │ - Calibrate │    │ - DDC       │ │
│  └──────┬──────┘    └─────────────┘    └─────────────┘    └──────┬──────┘ │
│         │                                                         │        │
│         │              SIGNAL FLOW (TAKER)                        │        │
│         ▼                                                         ▼        │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                         EXECUTION LAYER                              │  │
│  │                    (Order Management + Position Tracking)            │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│         ▲                                                         ▲        │
│         │              ORDER FLOW (MAKER)                         │        │
│         │                                                         │        │
│  ┌──────┴──────┐                                           ┌──────┴──────┐ │
│  │    MAKER    │                                           │   CONTEXT   │ │
│  │             │                                           │   PARSER    │ │
│  │ - LIP Farm  │                                           │             │ │
│  │ - FLB Exploit                                           │ - Ticker    │ │
│  │ - Inventory │                                           │ - Rules     │ │
│  └─────────────┘                                           └─────────────┘ │
│                                                                            │
├────────────────────────────────────────────────────────────────────────────┤
│                           KALSHI CLIENT                                     │
│                    (REST API + WebSocket + Auth)                           │
└────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    KALSHI API       │
                         │  (External Service) │
                         └─────────────────────┘
```

## 2.2 Concurrency Model

The system uses Python's `asyncio` with multiple concurrent loops:

```python
async def run_lifecycle(self):
    await asyncio.gather(
        self.run_taker_loop(),      # 500ms polling - whale signals
        self.run_maker_loop(),      # 1s cycle - LIP farming
        self.run_websocket_loop(),  # Real-time data streaming
        self.run_status_loop(),     # 5min status reports
    )
```

**Critical Design Decision:** When a whale signal is detected, the maker loop is paused (`self.maker_active = False`) to:
1. Free up capital/inventory for the taker trade
2. Prevent conflicting positions
3. Reduce API rate limit consumption

## 2.3 State Management

| State | Location | Persistence |
|-------|----------|-------------|
| Whale Profiles | `scanner.whale_profiles` | In-memory (lost on restart) |
| ML Model | `brain.model` | Pickled to `models/brain_model.pkl` |
| Whale Stats | `brain.whale_stats` | Pickled with model |
| Risk State | `risk_engine` | In-memory (resets on restart) |
| Positions | `risk_engine.positions` | In-memory |
| Active Quotes | `maker.active_quotes` | In-memory |

**GAP IDENTIFIED:** No persistent position tracking across restarts. If system crashes with open positions, they're orphaned.

---

# 3. Module Specifications

## 3.1 Kalshi Client

**File:** `modules/mimic_v3/kalshi_client.py`
**Lines:** ~450
**Purpose:** Interface with Kalshi's REST and WebSocket APIs

### 3.1.1 Authentication

Kalshi uses HMAC-SHA256 authentication:

```python
def _generate_signature(self, timestamp: str, method: str, path: str, body: str = "") -> str:
    message = f"{timestamp}{method}{path}{body}"
    signature = hmac.new(
        self.api_secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature
```

**Headers sent with every request:**
- `KALSHI-ACCESS-KEY`: Your API key
- `KALSHI-ACCESS-SIGNATURE`: HMAC signature
- `KALSHI-ACCESS-TIMESTAMP`: Unix timestamp in milliseconds

### 3.1.2 Rate Limiting

Implemented via token bucket algorithm:

```python
@dataclass
class RateLimiter:
    requests_per_second: float = 10.0  # Kalshi's limit
    tokens: float = 10.0
    last_update: float

    async def acquire(self):
        # Refill tokens based on elapsed time
        elapsed = now - self.last_update
        self.tokens = min(self.requests_per_second,
                         self.tokens + elapsed * self.requests_per_second)

        if self.tokens < 1:
            wait_time = (1 - self.tokens) / self.requests_per_second
            await asyncio.sleep(wait_time)
```

**Current Setting:** 10 requests/second (Kalshi's documented limit)

**POTENTIAL ISSUE:** Kalshi may have different limits for different endpoints. We use a single global limiter.

### 3.1.3 Circuit Breaker

Prevents cascade failures when Kalshi API is degraded:

```python
@dataclass
class CircuitBreaker:
    failure_threshold: int = 5      # Failures before opening
    reset_timeout: float = 60.0     # Seconds before retry
    state: str = "closed"           # closed, open, half-open
```

**States:**
- `closed`: Normal operation
- `open`: All requests blocked (after 5 failures)
- `half-open`: Allow 1 request to test recovery

### 3.1.4 REST Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/exchange/status` | GET | Check if exchange is operational |
| `/markets` | GET | List markets with filters |
| `/markets/{ticker}` | GET | Get single market details |
| `/events/{event_ticker}` | GET | Get event + settlement rules |
| `/markets/{ticker}/orderbook` | GET | Get orderbook depth |
| `/markets/{ticker}/trades` | GET | Get recent trades |
| `/portfolio/balance` | GET | Get account balance |
| `/portfolio/positions` | GET | Get open positions |
| `/portfolio/orders` | POST | Create new order |
| `/portfolio/orders/{id}` | DELETE | Cancel order |
| `/portfolio/fills` | GET | Get order fills |

### 3.1.5 WebSocket Channels

| Channel | Data | Use Case |
|---------|------|----------|
| `trade` | Real-time trades | Whale detection |
| `orderbook_delta` | Book updates | Spread monitoring |
| `fill` | Your order fills | Position tracking |
| `order` | Your order status | Order management |

**WebSocket URL:** `wss://api.elections.kalshi.com/trade-api/ws/v2`

### 3.1.6 Order Creation

```python
async def create_order(
    self,
    ticker: str,
    side: OrderSide,        # YES or NO
    order_type: OrderType,  # LIMIT or MARKET
    count: int,             # Number of contracts
    price: int = None,      # Cents (1-99) for limit orders
) -> Dict:
```

**IMPORTANT:** Kalshi prices are in cents (1-99), not decimals (0.01-0.99).

---

## 3.2 Context Parser

**File:** `modules/mimic_v3/context_parser.py`
**Lines:** ~280
**Purpose:** Parse Kalshi market data into LLM-friendly context

### 3.2.1 Ticker Parsing

Kalshi tickers follow patterns: `PREFIX-DATE-STRIKE`

Examples:
- `KXCPI-25DEC-T0.3` → CPI December 2025 above 0.3%
- `FED-25DEC-T3.75` → Fed Rate December 2025 at 3.75%
- `KXHIGHNY-25NOV21-T52` → NYC High Temp Nov 21 2025 above 52°F

**Ticker Map:**
```python
self.ticker_map = {
    "FED": "Federal Funds Rate",
    "CPI": "Consumer Price Index (CPI)",
    "KXCPI": "Consumer Price Index (CPI)",
    "INX": "S&P 500 Index",
    "KXU3": "U3 Unemployment Rate",
    "KXHIGH": "Daily High Temperature",
    "KXLOW": "Daily Low Temperature",
    # ... etc
}
```

### 3.2.2 Agency Extraction

Uses regex to find settlement source from rules text:

```python
self.agency_regex = re.compile(
    r"(?:released|published|reported|announced)\s+by\s+(?:the\s+)?([A-Z][a-zA-Z\s&]+?)(?:\.|,|;|\s+in\s+)",
    re.IGNORECASE
)
```

**Example:**
- Input: `"...data released by the Bureau of Labor Statistics in their..."`
- Output: `"Bureau of Labor Statistics"`

**Fallback Chain:**
1. Regex match on rules text
2. Check settlement_sources field
3. Keyword matching ("bls" → BLS, "fed" → Federal Reserve)
4. Default: "Official Issuer"

### 3.2.3 Search Query Generation

Converts ticker to natural language for Perplexity:

```python
def _generate_search_query(self, ticker, title, subtitle):
    # "KXCPI-25DEC-T0.3" → "Consumer Price Index (CPI) official data release December 2025 above 0.3 forecast"
```

### 3.2.4 LLM Context Compression

Reduces verbose Kalshi data to token-efficient format:

```python
def _compress_for_llm(self, title, agency, condition, subtitle):
    return f"Event: {title} ({subtitle}) | Source: {agency} | Condition: {condition}"
```

**Example Output:**
```
Event: CPI > 3.0% (December 2025) | Source: Bureau of Labor Statistics | Condition: CPI > 3.0%
```

### 3.2.5 Date Parsing Complexity

Kalshi uses inconsistent date formats:

| Format | Example | Meaning |
|--------|---------|---------|
| `25DEC` | Year + Month | December 2025 |
| `25DEC21` | Year + Month + Day | December 21, 2025 |
| `DEC25` | Month + Year | December 2025 |

**Current Implementation:** Try multiple formats, fall back to subtitle text.

**LIMITATION:** Doesn't handle all edge cases. Weather tickers especially complex.

---

## 3.3 Shadow Scanner

**File:** `modules/mimic_v3/scanner.py`
**Lines:** ~350
**Purpose:** Detect whale activity and classify trading strategies

### 3.3.1 Shadow ID Generation

Creates fingerprint for anonymous traders based on observable patterns:

```python
def _generate_shadow_id(self, trade_data: Dict) -> str:
    features = [
        str(trade_data.get("count", 0) // 10 * 10),  # Size bucket (10s)
        str(int(trade_data.get("yes_price", 50) // 5 * 5)),  # Price bucket (5s)
        trade_data.get("taker_side", "unknown"),
    ]
    feature_str = "|".join(features)
    hash_obj = hashlib.md5(feature_str.encode())
    return f"WHALE_{hash_obj.hexdigest()[:8].upper()}"
```

**CRITICAL LIMITATION:** This is a naive fingerprinting approach. Same shadow ID will be assigned to different traders with similar patterns. Production would need:
- Time-based clustering
- Cross-market correlation
- Order flow sequence analysis
- Machine learning-based entity resolution

### 3.3.2 Strategy Classification

```python
def _classify_strategy(self, trade, market, resolution_hours):
    price = trade.get("yes_price", 50) / 100.0
    volume = trade.get("count", 0) * price

    # ARBITRAGE: Near resolution + extreme price
    if resolution_hours < 2.0:
        if price > 0.95 or price < 0.05:
            return StrategyType.ARBITRAGE, 0.9  # High confidence
        if price > 0.85 or price < 0.15:
            return StrategyType.ARBITRAGE, 0.7

    # INFORMATIONAL: Large size at mid-range prices
    if volume > self.volume_threshold * 2 and 0.25 < price < 0.75:
        return StrategyType.INFORMATIONAL, 0.8

    return StrategyType.UNKNOWN, 0.3
```

**Strategy Types:**
| Type | Characteristics | Treatment |
|------|-----------------|-----------|
| `ARBITRAGE` | Near settlement, extreme prices | Fast lane (skip Oracle) |
| `INFORMATIONAL` | Large size, mid prices, away from settlement | Slow lane (Oracle validation) |
| `MARKET_MAKER` | Two-sided, passive | Ignored |
| `UNKNOWN` | Doesn't match patterns | Low confidence |

### 3.3.3 Whale Profile Tracking

```python
@dataclass
class WhaleProfile:
    shadow_id: str
    first_seen: datetime
    total_trades: int = 0
    winning_trades: int = 0
    total_volume: float = 0.0
    total_pnl: float = 0.0
    avg_size: float = 0.0
    strategy_signals: Dict[str, int]  # Strategy type counts

    @property
    def win_rate(self) -> float:
        return self.winning_trades / self.total_trades if self.total_trades > 0 else 0.5

    @property
    def edge_score(self) -> float:
        # Composite score: 70% win rate, 30% volume
        if self.total_trades < 5:
            return 0.5  # Not enough data
        return (self.win_rate * 0.7) + (min(1.0, self.total_volume / 100000) * 0.3)
```

### 3.3.4 Order Flow Imbalance

Measures directional pressure from recent trades:

```python
def _calculate_order_flow_imbalance(self, ticker: str) -> float:
    trades = self.recent_trades.get(ticker, [])[-50:]  # Last 50 trades

    yes_volume = sum(t["count"] for t in trades if t["taker_side"] == "yes")
    no_volume = sum(t["count"] for t in trades if t["taker_side"] == "no")

    total = yes_volume + no_volume
    return (yes_volume - no_volume) / total if total > 0 else 0.0
```

**Output:** -1.0 (all NO) to +1.0 (all YES)

### 3.3.5 Resolution Proximity

Calculates hours until market settlement:

```python
def _calculate_resolution_proximity(self, market: Dict) -> Optional[float]:
    close_time = market.get("close_time") or market.get("expected_expiration_time")
    # Parse and calculate hours until close
    delta = close_time - now
    return delta.total_seconds() / 3600.0
```

**Used for:**
- Arbitrage detection (< 2 hours = potential arb)
- Feature for ML model
- Urgency scoring

### 3.3.6 Signal Data Structure

```python
@dataclass
class WhaleSignal:
    shadow_id: str
    ticker: str
    event_ticker: str
    side: str                          # "yes" or "no"
    price: float                       # 0-1
    volume: float                      # Dollar amount
    strategy_type: StrategyType
    confidence: float                  # 0-1
    timestamp: datetime
    raw_market_data: Dict              # For Oracle
    resolution_proximity: Optional[float]  # Hours
    order_flow_imbalance: float        # -1 to 1
```

---

## 3.4 Mimic Brain

**File:** `modules/mimic_v3/brain.py`
**Lines:** ~320
**Purpose:** Online machine learning for win probability prediction

### 3.4.1 Why River (Online Learning)?

Traditional ML:
```
Collect data → Train batch model → Deploy → Model goes stale → Retrain
```

Online Learning (River):
```
Get observation → Predict → Get outcome → Update model → Repeat
```

**Advantages:**
- Adapts to regime changes in real-time
- No retraining downtime
- Memory efficient (no dataset storage)
- Handles concept drift

### 3.4.2 Model Pipeline

```python
def _build_pipeline(self):
    # Numerical features
    num_features = [
        'whale_win_rate',
        'whale_log_pnl',
        'sentiment_score',
        'implied_prob',
        'order_flow_imbalance',
        'resolution_hours',
        'volume_normalized',
        'confidence'
    ]

    num_pipe = compose.Select(*num_features) | preprocessing.StandardScaler()

    # Categorical features with target encoding
    cat_pipe = compose.Select('shadow_id', 'strategy_type') | feature_extraction.TargetEncoder(smoothing=10)

    # Combined model
    return (
        (num_pipe + cat_pipe) |
        linear_model.LogisticRegression(optimizer=optim.SGD(lr=0.05), l2=0.01)
    )
```

**Pipeline Structure:**
```
Input Features
      │
      ├── Numerical ──▶ StandardScaler ──┐
      │                                   │
      └── Categorical ─▶ TargetEncoder ──┤
                                          │
                                          ▼
                              LogisticRegression
                                          │
                                          ▼
                              P(win) ∈ [0, 1]
```

### 3.4.3 Feature Engineering

| Feature | Source | Calculation | Range |
|---------|--------|-------------|-------|
| `whale_win_rate` | Whale history | wins / total_trades | 0-1 |
| `whale_log_pnl` | Whale history | sign(pnl) * log(1 + \|pnl\|) | (-∞, +∞) |
| `sentiment_score` | Oracle | Perplexity sentiment | -1 to 1 |
| `implied_prob` | Market price | Price as probability | 0-1 |
| `order_flow_imbalance` | Scanner | (yes_vol - no_vol) / total | -1 to 1 |
| `resolution_hours` | Scanner | min(hours, 72) / 72 | 0-1 |
| `volume_normalized` | Trade | z-score of volume | (-∞, +∞) |
| `confidence` | Signal | Strategy confidence | 0-1 |
| `shadow_id` | Scanner | Target encoded | (-∞, +∞) |
| `strategy_type` | Scanner | Target encoded | (-∞, +∞) |

### 3.4.4 Target Encoding

For categorical features (shadow_id, strategy_type), we use target encoding:

```
TargetEncode(category) = (n * mean_category + m * global_mean) / (n + m)
```

Where:
- `n` = observations of this category
- `mean_category` = win rate for this category
- `m` = smoothing parameter (10)
- `global_mean` = overall win rate

**Why:** Converts categorical to numerical while encoding predictive information.

### 3.4.5 Learning Loop

```python
def learn(self, features: Dict, is_win: bool, pnl: float = 0.0):
    label = 1 if is_win else 0

    # Update River model (single observation)
    self.model.learn_one(features, label)

    # Update metrics
    pred_prob = self.predict(features)
    for metric in self.metrics.values():
        metric.update(label, pred_prob)

    # Store for calibration
    self.predictions.append((pred_prob, label))

    # Update whale stats
    self.whale_stats[shadow_id]["wins"] += 1 if is_win else 0
    self.whale_stats[shadow_id]["losses"] += 0 if is_win else 1
    self.whale_stats[shadow_id]["total_pnl"] += pnl
```

### 3.4.6 Probability Calibration

Raw model outputs may be miscalibrated. We apply simple binning calibration:

```python
def _calibrate(self, raw_prob: float) -> float:
    # Group historical predictions into bins
    bins = defaultdict(list)
    for pred, actual in self.predictions[-1000:]:
        bin_idx = int(pred * 10)  # 10 bins
        bins[bin_idx].append(actual)

    # Find actual win rate for this bin
    bin_idx = int(raw_prob * 10)
    if bin_idx in bins and len(bins[bin_idx]) > 10:
        actual_rate = sum(bins[bin_idx]) / len(bins[bin_idx])
        return 0.7 * raw_prob + 0.3 * actual_rate  # Blend

    return raw_prob
```

**LIMITATION:** Simple binning calibration. Could use Platt scaling or isotonic regression.

### 3.4.7 Model Persistence

```python
def _save_model(self):
    state = {
        "model": self.model,
        "whale_stats": dict(self.whale_stats),
        "predictions": self.predictions[-5000:],
        "feature_stats": {...},
        "saved_at": datetime.utcnow().isoformat()
    }
    with open(self.model_path, 'wb') as f:
        pickle.dump(state, f)
```

**Saved every 100 predictions** to `models/brain_model.pkl`

---

## 3.5 Risk Engine

**File:** `modules/mimic_v3/risk_engine.py`
**Lines:** ~380
**Purpose:** Position sizing and risk management

### 3.5.1 Asymptotic Kelly Criterion

Standard Kelly:
```
f* = (p*b - q) / b = p - q/b
```

Where:
- `f*` = fraction of bankroll to bet
- `p` = probability of win
- `q` = 1 - p (probability of loss)
- `b` = payout ratio (net odds)

**Problem:** Kelly assumes you know the true probability. With estimated probabilities, it overbets.

**Asymptotic Kelly** adjusts for estimation uncertainty:

```
f* = (p - q/b) / (1 + 1/n)
```

Where `n` = number of samples used to estimate `p`.

**Behavior:**
- n = 1: f* reduced by 50%
- n = 10: f* reduced by 9%
- n = 100: f* reduced by 1%
- n → ∞: approaches standard Kelly

```python
def calculate_position_size(self, win_prob, payout_ratio, conviction, estimation_samples, ...):
    q = 1 - win_prob
    edge = win_prob - (q / payout_ratio)

    if edge < self.min_edge_threshold:  # 2% minimum
        return 0.0, "Edge too small"

    # Standard Kelly
    kelly_f = edge / payout_ratio

    # Asymptotic adjustment
    asymptotic_factor = 1 / (1 + 1 / max(estimation_samples, 1))
    adjusted_kelly = kelly_f * asymptotic_factor

    # Fractional Kelly (25% by default)
    fractional_kelly = adjusted_kelly * self.kelly_fraction

    # Apply DDC and conviction
    raw_size = self.current_capital * fractional_kelly * ddc_multiplier * conviction

    return min(raw_size, max_position), "OK"
```

### 3.5.2 Dynamic Drawdown Control (DDC)

Reduces position size as drawdown increases:

```python
def _calculate_ddc_multiplier(self) -> float:
    drawdown = (self.peak_capital - self.current_capital) / self.peak_capital

    if drawdown >= 0.30:
        self.state = RiskState.HALTED
        return 0.0  # Stop trading

    if drawdown >= 0.20:
        self.state = RiskState.RESTRICTED
        return 0.5  # Half size

    if drawdown >= 0.10:
        self.state = RiskState.CAUTIOUS
        return max(0.5, 1.0 - (drawdown * 2))

    return 1.0 - drawdown  # Linear reduction
```

**DDC Curve:**
| Drawdown | Multiplier | State |
|----------|------------|-------|
| 0% | 1.0 | NORMAL |
| 5% | 0.95 | NORMAL |
| 10% | 0.80 | CAUTIOUS |
| 15% | 0.70 | CAUTIOUS |
| 20% | 0.50 | RESTRICTED |
| 25% | 0.50 | RESTRICTED |
| 30%+ | 0.00 | HALTED |

### 3.5.3 Position Limits

```python
# Per-position cap
max_position = self.current_capital * self.max_position_pct  # 10%

# Per-event cap (correlation management)
max_event = self.current_capital * self.max_event_exposure  # 25%
current_event_exposure = self.event_exposure.get(event_ticker, 0)
available_event = max(0, max_event - current_event_exposure)
```

### 3.5.4 Daily/Weekly Limits

```python
self.max_daily_loss = 50.00   # Hard stop
self.max_weekly_loss = 150.00

def update_equity(self, pnl):
    self.current_capital += pnl
    self.daily_pnl += pnl
    self.weekly_pnl += pnl

    if self.daily_pnl <= -self.max_daily_loss:
        self.state = RiskState.HALTED

    if self.weekly_pnl <= -self.max_weekly_loss:
        self.state = RiskState.HALTED
```

### 3.5.5 Risk States

```python
class RiskState(Enum):
    NORMAL = "NORMAL"         # Full trading
    CAUTIOUS = "CAUTIOUS"     # 10-20% drawdown
    RESTRICTED = "RESTRICTED" # 20-30% drawdown
    HALTED = "HALTED"         # >30% DD or daily/weekly limit
```

### 3.5.6 Payout Ratio Calculation

For binary options at price P:

**YES side:**
- Pay: P per contract
- Win: 1.00 per contract
- Payout ratio: (1 - P) / P

**NO side:**
- Pay: (1 - P) per contract
- Win: 1.00 per contract
- Payout ratio: P / (1 - P)

```python
if signal.side == "yes":
    payout_ratio = (1 - price) / price if price > 0 else 1.0
else:
    payout_ratio = price / (1 - price) if price < 1 else 1.0
```

**Example:** YES at $0.60
- Payout ratio = 0.40 / 0.60 = 0.67
- You risk $0.60 to win $0.40

---

## 3.6 News Oracle

**File:** `modules/mimic_v3/news_oracle.py`
**Lines:** ~300
**Purpose:** AI-powered sentiment analysis using Perplexity API

### 3.6.1 Perplexity API Integration

```python
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"

async def _call_perplexity(self, context, additional_context):
    async with session.post(
        self.PERPLEXITY_API_URL,
        headers={
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama-3.1-sonar-small-128k-online",  # Online search model
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 500,
            "return_citations": True
        }
    ) as response:
        data = await response.json()
```

### 3.6.2 System Prompt

```python
system_prompt = """You are a financial analyst AI. Analyze the latest news and data to provide sentiment analysis for prediction market events.

Your response must be valid JSON with this exact format:
{
    "sentiment_score": <float from -1.0 to 1.0>,
    "confidence": <float from 0.0 to 1.0>,
    "summary": "<brief 1-2 sentence summary>",
    "key_factors": ["<factor1>", "<factor2>"]
}

Sentiment scale:
- -1.0: Strongly bearish (event very unlikely)
- 0.0: Neutral/uncertain
- +1.0: Strongly bullish (event very likely)
"""
```

### 3.6.3 Caching

```python
@dataclass
class CacheEntry:
    result: SentimentResult
    expires_at: datetime

def _check_cache(self, query: str) -> Optional[SentimentResult]:
    key = hashlib.md5(query.lower().encode()).hexdigest()
    if key in self._cache:
        entry = self._cache[key]
        if datetime.utcnow() < entry.expires_at:
            return entry.result
    return None
```

**Cache TTL:** 15 minutes (configurable)

### 3.6.4 Rate Limiting

```python
rate_limit_rpm: int = 20  # Perplexity's limit

async def _check_rate_limit(self):
    now = datetime.utcnow()
    minute_ago = now - timedelta(minutes=1)
    self._request_times = [t for t in self._request_times if t > minute_ago]

    if len(self._request_times) >= self.rate_limit_rpm:
        wait_time = (self._request_times[0] - minute_ago).total_seconds()
        await asyncio.sleep(wait_time)
```

### 3.6.5 Mock Mode

For testing without API key:

```python
async def _mock_sentiment(self, context: Dict) -> SentimentResult:
    # Deterministic "sentiment" based on query hash
    query = context["search_query"]
    hash_val = int(hashlib.md5(query.encode()).hexdigest()[:8], 16)
    score = ((hash_val % 1000) / 500) - 1.0  # -1 to 1

    return SentimentResult(
        score=round(score, 3),
        confidence=0.3 + abs(score) * 0.4,
        summary=f"[MOCK] Simulated sentiment...",
        sources=["mock_source"],
        query_used=query
    )
```

### 3.6.6 Response Parsing

Handles various LLM output formats:

```python
def _parse_llm_response(self, content: str) -> Dict:
    # Try direct JSON parse
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Try markdown code block
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
    if json_match:
        return json.loads(json_match.group(1))

    # Try to find JSON object in text
    json_match = re.search(r'\{[^{}]*"sentiment_score"[^{}]*\}', content, re.DOTALL)
    if json_match:
        return json.loads(json_match.group(0))

    # Fallback
    return {"sentiment_score": 0.0, "confidence": 0.3, "summary": content[:200]}
```

---

## 3.7 Market Maker

**File:** `modules/mimic_v3/maker.py`
**Lines:** ~320
**Purpose:** Passive liquidity provision and LIP farming

### 3.7.1 LIP (Liquidity Incentive Program)

Kalshi offers rebates for providing liquidity on certain markets. The maker:
1. Identifies LIP-eligible markets
2. Posts limit orders at best bid
3. Earns rebates when orders fill

### 3.7.2 Favorite-Longshot Bias (FLB)

Research shows prediction markets systematically:
- **Overprice longshots** (low probability events)
- **Underprice favorites** (high probability events)

```python
def _calculate_opportunity_score(self, spread_bps, lip_eligible, volume_24h, favorite_price):
    score = 0.0

    # Wider spread = better for MM
    score += min(spread_bps / 100, 10)

    # LIP bonus
    if lip_eligible:
        score += 5.0

    # Moderate volume is best
    if 1000 < volume_24h < 50000:
        score += 3.0

    # FLB: Strong favorites have edge
    if favorite_price > 0.70 or favorite_price < 0.30:
        score += 2.0

    return score
```

### 3.7.3 Inventory Management

```python
max_inventory_per_market: int = 100  # Contracts
max_total_inventory: int = 500

def _check_inventory_room(self, ticker: str) -> bool:
    current = abs(self.inventory.get(ticker, 0))
    total = sum(abs(v) for v in self.inventory.values())

    return (
        current < self.max_inventory_per_market and
        total < self.max_total_inventory
    )
```

### 3.7.4 Quote Management

```python
async def _quote_market(self, opp: MarketOpportunity):
    # Get orderbook
    orderbook = await self.client.get_orderbook(ticker)

    # Quote at best bid on favorite side
    if opp.favorite_side == "yes":
        best_bid = orderbook["yes"][0][0]
        side = OrderSide.YES
    else:
        best_bid = orderbook["no"][0][0]
        side = OrderSide.NO

    # Place limit order
    await self.client.create_order(
        ticker=ticker,
        side=side,
        order_type=OrderType.LIMIT,
        count=10,  # Start with 10 contracts
        price=best_bid
    )
```

### 3.7.5 Quote Lifecycle

1. **Scan** for opportunities (every cycle)
2. **Quote** on top 5 opportunities
3. **Manage** existing quotes (cancel stale after 5 min)
4. **Track** fills and update inventory

---

## 3.8 Central Cortex

**File:** `main_mimic.py`
**Lines:** ~380
**Purpose:** Orchestrate all components

### 3.8.1 Initialization Sequence

```python
async def initialize(self):
    # 1. Load environment variables
    load_dotenv()

    # 2. Create Kalshi client
    self.client = KalshiClient(
        api_key=os.getenv("KALSHI_API_KEY"),
        api_secret=os.getenv("KALSHI_API_SECRET"),
        demo_mode=self.demo_mode
    )
    await self.client.connect()

    # 3. Wire up components
    self.scanner.client = self.client
    self.maker.client = self.client
    self.scanner.setup_websocket_handlers(self.client)

    # 4. Create directories
    os.makedirs("models", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
```

### 3.8.2 Signal Processing Pipeline

```python
async def handle_whale_signal(self, signal):
    # 1. ORACLE CHECK (Slow Lane only)
    sentiment_score = 0.0
    if signal.strategy_type == StrategyType.INFORMATIONAL:
        oracle_result = await self.oracle.get_sentiment_snapshot(signal.raw_market_data)
        sentiment_score = oracle_result.score

    # 2. FEATURE ENGINEERING & PREDICTION
    features = self.brain.extract_features(signal, sentiment_score)
    win_prob = self.brain.predict(features)

    # 3. RISK ENGINE SIZING
    payout_ratio = (1 - signal.price) / signal.price  # For YES side

    size, reason = self.risk_manager.calculate_position_size(
        win_prob=win_prob,
        payout_ratio=payout_ratio,
        conviction=signal.confidence,
        estimation_samples=whale_trade_count,
        ticker=signal.ticker,
        event_ticker=signal.event_ticker
    )

    if size <= 0:
        return  # Rejected

    # 4. EXECUTION
    await self.execute_trade(signal, size, features, win_prob)
```

### 3.8.3 Concurrent Loops

| Loop | Frequency | Purpose |
|------|-----------|---------|
| Taker | 500ms | Poll for whale signals, process pipeline |
| Maker | 1s | Run LIP farming cycle |
| WebSocket | Real-time | Stream market data |
| Status | 5min | Log system status |

### 3.8.4 Graceful Shutdown

```python
async def shutdown(self):
    self.running = False
    self.shutdown_event.set()

    # Cancel all maker quotes
    await self.maker.cancel_all_quotes()

    # Close connections
    await self.client.close()
    await self.oracle.close()

    # Save brain model
    self.brain._save_model()
```

---

# 4. Data Flows

## 4.1 Whale Signal Flow

```
┌─────────────────┐
│ Kalshi WebSocket│
│    (trades)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    SCANNER      │
│ - Volume check  │
│ - Shadow ID     │
│ - Strategy class│
└────────┬────────┘
         │ WhaleSignal
         ▼
┌─────────────────┐     ┌─────────────────┐
│  FAST LANE?     │─YES─│   SKIP ORACLE   │
│  (Arbitrage)    │     └────────┬────────┘
└────────┬────────┘              │
         │ NO                    │
         ▼                       │
┌─────────────────┐              │
│    ORACLE       │              │
│ - Perplexity    │              │
│ - Sentiment     │              │
└────────┬────────┘              │
         │                       │
         └───────────┬───────────┘
                     │
                     ▼
            ┌─────────────────┐
            │     BRAIN       │
            │ - Features      │
            │ - Predict P(win)│
            └────────┬────────┘
                     │
                     ▼
            ┌─────────────────┐
            │  RISK ENGINE    │
            │ - Kelly size    │
            │ - DDC adjust    │
            │ - Limits check  │
            └────────┬────────┘
                     │
                     ▼
            ┌─────────────────┐
            │   EXECUTION     │
            │ - Create order  │
            │ - Track position│
            └────────┬────────┘
                     │
                     ▼
            ┌─────────────────┐
            │  SETTLEMENT     │
            │ - Get outcome   │
            │ - Update Brain  │
            │ - Update Risk   │
            │ - Update Scanner│
            └─────────────────┘
```

## 4.2 Feature Data Flow

```
Signal Attributes          External Data           Historical Data
      │                          │                       │
      │                          │                       │
      ▼                          ▼                       ▼
┌───────────┐            ┌───────────┐           ┌───────────┐
│ - ticker  │            │ Oracle    │           │ whale_stats│
│ - price   │            │ sentiment │           │ - win_rate │
│ - volume  │            │ - score   │           │ - pnl     │
│ - side    │            │ - conf    │           │ - trades  │
│ - strategy│            └─────┬─────┘           └─────┬─────┘
│ - resol_hr│                  │                       │
└─────┬─────┘                  │                       │
      │                        │                       │
      └────────────────────────┼───────────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   FEATURE VECTOR    │
                    ├─────────────────────┤
                    │ whale_win_rate      │
                    │ whale_log_pnl       │
                    │ sentiment_score     │
                    │ implied_prob        │
                    │ order_flow_imbalance│
                    │ resolution_hours    │
                    │ volume_normalized   │
                    │ confidence          │
                    │ shadow_id (encoded) │
                    │ strategy (encoded)  │
                    └─────────────────────┘
```

---

# 5. Algorithms & Formulas

## 5.1 Kelly Criterion Variants

### Standard Kelly
```
f* = (p*b - q) / b = p - q/b

Where:
  f* = optimal fraction of bankroll
  p  = probability of win
  q  = 1 - p = probability of loss
  b  = payout ratio (net odds)
```

### Asymptotic Kelly (Implemented)
```
f* = (p - q/b) / (1 + 1/n)

Where:
  n = number of samples used to estimate p

Derivation: Accounts for estimation error in p
```

### Fractional Kelly (Applied)
```
f_actual = f* × fraction

Default fraction = 0.25 (Quarter Kelly)
```

### Kelly with Variance (Alternative - NOT implemented)
```
f* = f_kelly × (1 - var(p) × sensitivity)

Where:
  sensitivity = (1 + 1/b) / b
```

## 5.2 DDC Multiplier

```
DDC(d) = {
  0.0,           if d >= 0.30
  0.5,           if d >= 0.20
  max(0.5, 1-2d) if d >= 0.10
  1 - d,         otherwise
}

Where d = (peak - current) / peak
```

## 5.3 Target Encoding

```
TE(category) = (n × mean_cat + m × mean_global) / (n + m)

Where:
  n = observations of category
  mean_cat = target mean for category
  m = smoothing parameter (default 10)
  mean_global = overall target mean
```

## 5.4 Order Flow Imbalance

```
OFI = (V_yes - V_no) / (V_yes + V_no)

Where:
  V_yes = volume of YES taker trades
  V_no  = volume of NO taker trades

Range: [-1, +1]
```

## 5.5 Opportunity Score (Maker)

```
Score = min(spread_bps/100, 10)
      + 5 × is_lip
      + 3 × is_moderate_volume
      + 2 × is_extreme_favorite
```

---

# 6. Known Limitations

## 6.1 Critical Gaps

| Gap | Impact | Severity |
|-----|--------|----------|
| No position persistence | Orphaned positions on crash | HIGH |
| Naive shadow ID fingerprinting | Same ID for different traders | HIGH |
| No real settlement tracking | Paper trading uses simulation | HIGH |
| Single rate limiter | May hit endpoint-specific limits | MEDIUM |
| No order book depth analysis | Missing liquidity signals | MEDIUM |

## 6.2 Algorithmic Limitations

| Limitation | Current State | Ideal State |
|------------|---------------|-------------|
| Feature set | 10 features | Orderbook microstructure, cross-market |
| Model | Linear LogReg | Ensemble, gradient boosting |
| Calibration | Simple binning | Platt scaling, isotonic |
| Whale ID | Hash-based | ML entity resolution |
| Sentiment | Single LLM call | Multi-source aggregation |

## 6.3 Operational Limitations

- No monitoring/alerting infrastructure
- No backtesting framework
- No A/B testing for strategy variants
- No automated parameter tuning
- Logs only (no metrics/dashboards)

---

# 7. Potential Improvements

## 7.1 High Priority

### 7.1.1 Position Persistence
```python
# Add SQLite or PostgreSQL for position tracking
class PositionStore:
    def save_position(self, position: Position)
    def load_positions(self) -> List[Position]
    def update_on_fill(self, order_id, fill_data)
```

### 7.1.2 Improved Shadow ID
```python
# ML-based entity resolution
class WhaleIdentifier:
    def __init__(self):
        self.clustering_model = HDBSCAN()
        self.sequence_model = LSTM()

    def identify(self, trade_sequence) -> str:
        # Cluster by trading patterns
        # Use sequence model for temporal patterns
```

### 7.1.3 Real Settlement Tracking
```python
# WebSocket handler for settlements
@client.on_message("settlement")
async def handle_settlement(data):
    ticker = data["market_ticker"]
    outcome = data["result"]  # "yes" or "no"

    # Close positions, update Brain, update Scanner
```

## 7.2 Medium Priority

### 7.2.1 Orderbook Features
```python
features.update({
    "bid_depth_5": sum of top 5 bid sizes,
    "ask_depth_5": sum of top 5 ask sizes,
    "bid_ask_imbalance": (bid_depth - ask_depth) / total,
    "spread_bps": (best_ask - best_bid) / mid * 10000,
    "microprice": weighted mid by size,
})
```

### 7.2.2 Cross-Market Signals
```python
# Related market analysis
class CrossMarketAnalyzer:
    def get_related_markets(self, ticker) -> List[str]
    def calculate_correlation(self, ticker1, ticker2) -> float
    def detect_arbitrage(self, markets) -> List[ArbOpportunity]
```

### 7.2.3 Ensemble Model
```python
from river import ensemble

model = ensemble.ADWINBaggingClassifier(
    model=linear_model.LogisticRegression(),
    n_models=10,
    seed=42
)
```

## 7.3 Lower Priority

### 7.3.1 Backtesting Framework
```python
class Backtester:
    def __init__(self, historical_data: pd.DataFrame)
    def run(self, strategy: Strategy) -> BacktestResults
    def analyze(self, results) -> Dict[str, float]
```

### 7.3.2 Parameter Optimization
```python
from optuna import create_study

def objective(trial):
    kelly_fraction = trial.suggest_float("kelly_fraction", 0.1, 0.5)
    volume_threshold = trial.suggest_float("volume_threshold", 100, 2000)
    # Run backtest, return Sharpe ratio
```

### 7.3.3 Monitoring Dashboard
```python
# Prometheus metrics + Grafana
from prometheus_client import Counter, Gauge, Histogram

signals_processed = Counter('mimic_signals_total', 'Total signals processed')
capital_gauge = Gauge('mimic_capital', 'Current capital')
latency_histogram = Histogram('mimic_signal_latency', 'Signal processing latency')
```

---

# 8. Research Questions

## 8.1 For Your Team to Investigate

1. **Shadow ID Accuracy**: How well does our hash-based fingerprinting actually identify unique traders? What's the collision rate?

2. **Whale Edge Decay**: Do whale signals have predictive power? Does it decay over time (information gets priced in)?

3. **Sentiment Alpha**: Is Perplexity sentiment actually predictive, or just correlated with price? What's the lead time?

4. **Kelly Sizing**: Is Asymptotic Kelly the right choice? Should we use:
   - Fractional Kelly with fixed fraction?
   - Optimal f based on historical distribution?
   - Kelly with uncertainty bounds?

5. **Feature Importance**: Which features actually drive predictions? Is the model learning real patterns or noise?

6. **Market Regime**: Do strategies work differently in different market conditions (high volatility, news events, etc.)?

7. **Maker vs Taker**: What's the optimal capital allocation between LIP farming and whale following?

8. **Resolution Arb**: How often does the "fast lane" actually capture arbitrage opportunities?

## 8.2 Data to Collect

- Signal → Outcome pairs with full feature vectors
- Whale ID → Performance time series
- Sentiment score → Price movement correlation
- Fill rates and slippage by market/time
- Drawdown events and recovery patterns

## 8.3 Experiments to Run

1. **A/B test**: Oracle validation vs no validation for INFORMATIONAL signals
2. **Ablation study**: Remove each feature, measure impact on accuracy
3. **Hyperparameter sweep**: Kelly fraction, volume threshold, DDC curve
4. **Model comparison**: LogReg vs Random Forest vs Gradient Boosting (in River)
5. **Time decay**: Add trade recency weighting to whale stats

---

# Appendix A: File Inventory

| File | Lines | Purpose |
|------|-------|---------|
| `main_mimic.py` | 380 | Central orchestrator |
| `modules/mimic_v3/kalshi_client.py` | 450 | API client |
| `modules/mimic_v3/scanner.py` | 350 | Whale detection |
| `modules/mimic_v3/brain.py` | 320 | ML prediction |
| `modules/mimic_v3/risk_engine.py` | 380 | Position sizing |
| `modules/mimic_v3/news_oracle.py` | 300 | Sentiment analysis |
| `modules/mimic_v3/maker.py` | 320 | Market making |
| `modules/mimic_v3/context_parser.py` | 280 | Kalshi parsing |
| **Total** | **~2,780** | |

# Appendix B: Configuration Reference

| Parameter | Default | Location | Description |
|-----------|---------|----------|-------------|
| `KALSHI_API_KEY` | - | .env | API authentication |
| `KALSHI_API_SECRET` | - | .env | API authentication |
| `PERPLEXITY_API_KEY` | - | .env | Sentiment API |
| `INITIAL_CAPITAL` | 1000.0 | .env | Starting capital |
| `MAX_DAILY_LOSS` | 50.0 | .env | Daily stop loss |
| `MAX_WEEKLY_LOSS` | 150.0 | .env | Weekly stop loss |
| `KELLY_FRACTION` | 0.25 | .env | Fractional Kelly |
| `WHALE_VOLUME_THRESHOLD` | 500.0 | .env | Min whale trade size |
| `MIN_EDGE_THRESHOLD` | 0.02 | risk_engine | Min edge to trade |
| `MAX_POSITION_PCT` | 0.10 | risk_engine | Per-position cap |
| `MAX_EVENT_EXPOSURE` | 0.25 | risk_engine | Per-event cap |
| `CACHE_TTL_MINUTES` | 15 | news_oracle | Sentiment cache |
| `RATE_LIMIT_RPM` | 20 | news_oracle | Perplexity rate limit |

---

**Document Prepared By:** MIMIC Development Team
**For:** Research Review
**Classification:** Internal Use Only
