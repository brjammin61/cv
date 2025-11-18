# Kalshi Trading Dashboard - Developer Brief

**Goal:** Build a beautiful, production-ready trading dashboard for Kalshi markets, using the MonadPulse architecture as the foundation.

---

## 📊 What is Kalshi?

Kalshi is a regulated prediction market exchange where users trade on real-world events (elections, weather, economic data, etc.). Think: "Will unemployment be above 4%?" or "Will Bitcoin hit $100k by Dec 31?"

---

## 🎯 Project Overview

Build a real-time dashboard that:
1. Shows **active Kalshi markets** with live prices
2. Displays **trading opportunities** (arbitrage, mispricing)
3. Tracks **portfolio performance** (P&L, ROI, win rate)
4. Provides **market analytics** (volume, liquidity, spreads)

**Reference:** The MonadPulse validator dashboard architecture (React + FastAPI + PostgreSQL)

---

## 🏗️ Architecture (Copy MonadPulse Pattern)

```
┌─────────────────┐
│  React Frontend │ (Beautiful dashboard UI)
│  Port 3000      │
└────────┬────────┘
         │ HTTP API calls
         ↓
┌─────────────────┐
│   FastAPI       │ (REST API backend)
│   Port 8000     │
└────────┬────────┘
         │ SQL queries
         ↓
┌─────────────────┐      ┌──────────────┐
│  PostgreSQL DB  │ ←────┤  Ingestor    │
│  Port 5432      │      │  Service     │
└─────────────────┘      └──────┬───────┘
                                │
                                ↓
                      ┌──────────────────┐
                      │ Kalshi API       │
                      │ (Live market data)│
                      └──────────────────┘
```

---

## 📁 Project Structure

Create this exact structure:

```
kalshi_dashboard/
├── backend/
│   ├── api/
│   │   ├── main.py              # FastAPI server
│   │   ├── models.py            # Database models
│   │   ├── requirements.txt     # Python deps
│   │   └── Dockerfile
│   ├── ingestor/
│   │   ├── ingestor.py          # Fetches Kalshi data
│   │   ├── kalshi_client.py     # Kalshi API wrapper
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── docker-compose.yml       # Orchestration
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.js               # Main dashboard
│   │   ├── components/
│   │   │   ├── MarketCard.js
│   │   │   ├── PortfolioStats.js
│   │   │   └── OpportunityTable.js
│   │   └── index.js
│   ├── package.json
│   └── tailwind.config.js
└── README.md
```

---

## 🎨 Frontend Design (Copy MonadPulse Style)

**Reference:** MonadPulse React dashboard

### Technology Stack:
- React 18.2
- Tailwind CSS (for styling)
- Recharts (for charts)
- Lucide React (for icons)

### Layout:

```
┌─────────────────────────────────────────────────────────┐
│  Kalshi Dashboard - Live Markets                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐│
│  │Portfolio │  │Win Rate  │  │Active    │  │24h Vol  ││
│  │$12,450   │  │68%       │  │Markets   │  │$2.4M    ││
│  │+5.2%     │  │↑ 3%      │  │847       │  │↑ 12%    ││
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘│
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Portfolio Performance (7 Days)                    │ │
│  │  [Line chart showing P&L over time]                │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Top Trading Opportunities                         │ │
│  │  ┌────┬─────────────┬──────┬──────┬────────────┐  │ │
│  │  │#   │Market       │ Price│ Edge │ Expected ROI│  │ │
│  │  ├────┼─────────────┼──────┼──────┼────────────┤  │ │
│  │  │1   │BTC > 100k   │ 0.45 │+12%  │ $450       │  │ │
│  │  │2   │Unemp < 4%   │ 0.68 │+8%   │ $320       │  │ │
│  │  └────┴─────────────┴──────┴──────┴────────────┘  │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Color Scheme (Match MonadPulse):
- Background: Dark gray (`bg-gray-900`)
- Cards: Darker gray (`bg-gray-800`)
- Text: White (`text-white`)
- Accents: Blue/Green for positive, Red for negative
- Borders: Subtle gray (`border-gray-700`)

---

## 🔧 Backend Implementation

### 1. Database Models (backend/api/models.py)

```python
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Market(Base):
    """Kalshi market data"""
    __tablename__ = "markets"
    
    id = Column(Integer, primary_key=True)
    ticker = Column(String, unique=True, nullable=False)  # e.g., "BTC-100K-DEC31"
    title = Column(String)  # "Bitcoin above $100k by Dec 31"
    yes_price = Column(Float)  # Current YES price (0-1)
    no_price = Column(Float)   # Current NO price (0-1)
    volume_24h = Column(Float)  # 24h trading volume
    liquidity = Column(Float)   # Available liquidity
    category = Column(String)   # "crypto", "politics", "economics"
    closes_at = Column(DateTime)  # Market close time
    last_updated = Column(DateTime, default=datetime.utcnow)

class Trade(Base):
    """User trades"""
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True)
    market_ticker = Column(String)
    side = Column(String)  # "YES" or "NO"
    quantity = Column(Integer)  # Number of contracts
    entry_price = Column(Float)
    exit_price = Column(Float, nullable=True)
    pnl = Column(Float, nullable=True)
    status = Column(String)  # "open", "closed"
    opened_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)

class PortfolioStats(Base):
    """Daily portfolio statistics"""
    __tablename__ = "portfolio_stats"
    
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=datetime.utcnow)
    total_value = Column(Float)
    daily_pnl = Column(Float)
    win_rate = Column(Float)
    active_positions = Column(Integer)
```

### 2. FastAPI Endpoints (backend/api/main.py)

```python
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import models

app = FastAPI(title="Kalshi Dashboard API")

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/stats/kpi")
def get_kpi_stats(db: Session = Depends(get_db)):
    """Get dashboard KPI cards data"""
    latest_stats = db.query(models.PortfolioStats).order_by(
        models.PortfolioStats.date.desc()
    ).first()
    
    active_markets = db.query(models.Market).count()
    total_volume = db.query(func.sum(models.Market.volume_24h)).scalar()
    
    return {
        "portfolio_value": latest_stats.total_value,
        "portfolio_change_pct": latest_stats.daily_pnl / latest_stats.total_value * 100,
        "win_rate": latest_stats.win_rate,
        "active_markets": active_markets,
        "volume_24h": total_volume
    }

@app.get("/markets/top")
def get_top_markets(limit: int = 20, db: Session = Depends(get_db)):
    """Get top trading opportunities"""
    markets = db.query(models.Market).order_by(
        models.Market.volume_24h.desc()
    ).limit(limit).all()
    
    return [
        {
            "ticker": m.ticker,
            "title": m.title,
            "yes_price": m.yes_price,
            "volume_24h": m.volume_24h,
            "category": m.category
        }
        for m in markets
    ]

@app.get("/portfolio/history")
def get_portfolio_history(days: int = 7, db: Session = Depends(get_db)):
    """Get portfolio performance chart data"""
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    stats = db.query(models.PortfolioStats).filter(
        models.PortfolioStats.date >= cutoff
    ).order_by(models.PortfolioStats.date).all()
    
    return [
        {
            "date": s.date.strftime("%Y-%m-%d"),
            "value": s.total_value,
            "pnl": s.daily_pnl
        }
        for s in stats
    ]
```

### 3. Kalshi Data Ingestor (backend/ingestor/ingestor.py)

```python
import time
import logging
from kalshi_client import KalshiClient
from models import Market, PortfolioStats
from db_utils import get_db_session

logger = logging.getLogger(__name__)

def fetch_and_update_markets():
    """Fetch latest market data from Kalshi API"""
    client = KalshiClient(
        api_key=os.getenv('KALSHI_API_KEY'),
        api_secret=os.getenv('KALSHI_API_SECRET')
    )
    
    # Fetch all active markets
    markets_data = client.get_markets(status='active')
    
    db = get_db_session()
    
    for market_data in markets_data:
        # Update or create market record
        market = db.query(Market).filter(
            Market.ticker == market_data['ticker']
        ).first()
        
        if market:
            # Update existing
            market.yes_price = market_data['yes_bid']
            market.no_price = market_data['no_bid']
            market.volume_24h = market_data['volume']
            market.last_updated = datetime.utcnow()
        else:
            # Create new
            market = Market(
                ticker=market_data['ticker'],
                title=market_data['title'],
                yes_price=market_data['yes_bid'],
                no_price=market_data['no_bid'],
                volume_24h=market_data['volume'],
                category=market_data['category'],
                closes_at=market_data['close_time']
            )
            db.add(market)
    
    db.commit()
    logger.info(f"Updated {len(markets_data)} markets")

def main():
    """Main ingestor loop"""
    logger.info("Starting Kalshi ingestor...")
    
    while True:
        try:
            fetch_and_update_markets()
            time.sleep(60)  # Update every 60 seconds
        except Exception as e:
            logger.error(f"Error in ingestor: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
```

### 4. Kalshi API Client (backend/ingestor/kalshi_client.py)

```python
import requests
import hmac
import hashlib
import time

class KalshiClient:
    """Wrapper for Kalshi REST API"""
    
    BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = requests.Session()
    
    def _sign_request(self, method: str, path: str, body: str = ""):
        """Sign API request with HMAC"""
        timestamp = str(int(time.time() * 1000))
        message = f"{timestamp}{method}{path}{body}"
        signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return {
            'KALSHI-ACCESS-KEY': self.api_key,
            'KALSHI-ACCESS-SIGNATURE': signature,
            'KALSHI-ACCESS-TIMESTAMP': timestamp
        }
    
    def get_markets(self, status='active'):
        """Get all markets"""
        path = f"/markets?status={status}"
        headers = self._sign_request('GET', path)
        
        response = self.session.get(
            f"{self.BASE_URL}{path}",
            headers=headers
        )
        
        return response.json()['markets']
    
    def get_portfolio(self):
        """Get user portfolio"""
        path = "/portfolio/positions"
        headers = self._sign_request('GET', path)
        
        response = self.session.get(
            f"{self.BASE_URL}{path}",
            headers=headers
        )
        
        return response.json()
```

---

## ⚛️ React Frontend (Adapt MonadPulse UI)

### Main Dashboard (frontend/src/App.js)

```javascript
import React, { useState, useEffect } from 'react';
import { TrendingUp, Activity, DollarSign, BarChart3 } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [kpi, setKpi] = useState(null);
  const [portfolioHistory, setPortfolioHistory] = useState([]);
  const [topMarkets, setTopMarkets] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [kpiRes, historyRes, marketsRes] = await Promise.all([
          fetch(`${API_BASE_URL}/stats/kpi`),
          fetch(`${API_BASE_URL}/portfolio/history`),
          fetch(`${API_BASE_URL}/markets/top`)
        ]);

        setKpi(await kpiRes.json());
        setPortfolioHistory(await historyRes.json());
        setTopMarkets(await marketsRes.json());
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5000); // Refresh every 5s
    return () => clearInterval(interval);
  }, []);

  if (!kpi) return <div className="flex items-center justify-center h-screen bg-gray-900 text-white">Loading...</div>;

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <h1 className="text-4xl font-bold mb-8">Kalshi Trading Dashboard</h1>

        {/* KPI Cards */}
        <div className="grid grid-cols-4 gap-6 mb-8">
          <KpiCard 
            icon={<DollarSign />}
            title="Portfolio Value"
            value={`$${kpi.portfolio_value.toLocaleString()}`}
            change={kpi.portfolio_change_pct}
          />
          <KpiCard 
            icon={<TrendingUp />}
            title="Win Rate"
            value={`${kpi.win_rate.toFixed(1)}%`}
          />
          <KpiCard 
            icon={<Activity />}
            title="Active Markets"
            value={kpi.active_markets}
          />
          <KpiCard 
            icon={<BarChart3 />}
            title="24h Volume"
            value={`$${(kpi.volume_24h / 1000000).toFixed(1)}M`}
          />
        </div>

        {/* Portfolio Chart */}
        <div className="bg-gray-800 rounded-lg p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Portfolio Performance (7 Days)</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={portfolioHistory}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="date" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: 'none' }} />
              <Line type="monotone" dataKey="value" stroke="#3B82F6" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Top Markets Table */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Top Trading Opportunities</h2>
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="text-left py-3">Market</th>
                <th className="text-right py-3">YES Price</th>
                <th className="text-right py-3">24h Volume</th>
                <th className="text-left py-3">Category</th>
              </tr>
            </thead>
            <tbody>
              {topMarkets.map((market, i) => (
                <tr key={i} className="border-b border-gray-700 hover:bg-gray-700">
                  <td className="py-3">{market.title}</td>
                  <td className="text-right">${market.yes_price.toFixed(2)}</td>
                  <td className="text-right">${(market.volume_24h / 1000).toFixed(1)}k</td>
                  <td>
                    <span className="px-2 py-1 bg-blue-900 text-blue-300 rounded text-sm">
                      {market.category}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function KpiCard({ icon, title, value, change }) {
  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <div className="flex items-center mb-2">
        {icon}
        <span className="ml-2 text-gray-400 text-sm">{title}</span>
      </div>
      <div className="text-2xl font-bold">{value}</div>
      {change !== undefined && (
        <div className={`text-sm ${change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
          {change >= 0 ? '↑' : '↓'} {Math.abs(change).toFixed(2)}%
        </div>
      )}
    </div>
  );
}

export default App;
```

---

## 🚀 Deployment (Copy MonadPulse Process)

### 1. Docker Compose Setup (backend/docker-compose.yml)

```yaml
version: '3.8'

services:
  db:
    image: postgres:14-alpine
    environment:
      POSTGRES_USER: trader
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: kalshi_dashboard
    volumes:
      - db-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  api:
    build: ./api
    depends_on:
      - db
    environment:
      DATABASE_URL: postgresql://trader:${DB_PASSWORD}@db/kalshi_dashboard
    ports:
      - "8000:8000"

  ingestor:
    build: ./ingestor
    depends_on:
      - db
    environment:
      DATABASE_URL: postgresql://trader:${DB_PASSWORD}@db/kalshi_dashboard
      KALSHI_API_KEY: ${KALSHI_API_KEY}
      KALSHI_API_SECRET: ${KALSHI_API_SECRET}

volumes:
  db-data:
```

### 2. Environment Variables (.env)

```bash
DB_PASSWORD=your_secure_password
KALSHI_API_KEY=your_kalshi_api_key
KALSHI_API_SECRET=your_kalshi_api_secret
```

### 3. Launch Commands

```bash
# Backend
cd backend
docker-compose up -d --build

# Frontend
cd frontend
npm install
npm start
```

---

## 📋 Implementation Checklist

### Phase 1: Setup (Day 1)
- [ ] Create project structure
- [ ] Set up Docker environment
- [ ] Create PostgreSQL database
- [ ] Implement database models

### Phase 2: Backend (Day 2-3)
- [ ] Build FastAPI endpoints
- [ ] Implement Kalshi API client
- [ ] Create data ingestor
- [ ] Test API with Postman

### Phase 3: Frontend (Day 4-5)
- [ ] Build React dashboard UI
- [ ] Implement KPI cards
- [ ] Add portfolio chart
- [ ] Create markets table
- [ ] Style with Tailwind CSS

### Phase 4: Integration (Day 6)
- [ ] Connect frontend to backend
- [ ] Test live data flow
- [ ] Implement auto-refresh
- [ ] Fix any bugs

### Phase 5: Deployment (Day 7)
- [ ] Deploy to VPS (same as MonadPulse)
- [ ] Configure Nginx
- [ ] Set up SSL
- [ ] Monitor logs

---

## 🔑 Kalshi API Access

You'll need Kalshi API credentials:

1. Sign up at https://kalshi.com
2. Go to API settings
3. Generate API key + secret
4. Add to `.env` file

**API Docs:** https://trading-api.readme.io/reference/getting-started

---

## 💡 Key Differences from MonadPulse

| MonadPulse | Kalshi Dashboard |
|------------|------------------|
| Validator leaderboard | Market opportunities |
| MEV efficiency scores | Win rate / ROI tracking |
| Network statistics | Portfolio performance |
| Blockchain data | Prediction market data |
| Monad SDK | Kalshi API |

**Same architecture, different data source.**

---

## 🎯 Success Criteria

When done, you should have:
- ✅ Live dashboard showing Kalshi markets
- ✅ Real-time price updates (every 5s)
- ✅ Portfolio tracking with P&L
- ✅ Beautiful UI (matches MonadPulse style)
- ✅ Deployed to production VPS
- ✅ Auto-updating data ingestor

---

## 📚 Reference Code

**Study these MonadPulse files:**
- `monadpulse_frontend/src/App.js` - Dashboard layout
- `monadpulse_backend/api/main.py` - API structure
- `monadpulse_backend/ingestor/ingestor.py` - Data fetching pattern
- `monadpulse_backend/docker-compose.yml` - Deployment

**Adapt for Kalshi, but keep the same structure.**

---

## ⏱️ Timeline

- **Day 1-3:** Backend implementation
- **Day 4-6:** Frontend development
- **Day 7:** Deployment & testing

**Total:** 1 week for MVP

---

## 🚨 Important Notes

1. **Kalshi API has rate limits** - Cache data, don't spam API
2. **Use same tech stack** as MonadPulse (React, FastAPI, PostgreSQL)
3. **Same deployment pattern** - Docker Compose, VPS, Nginx
4. **Focus on MVP first** - Get basic version working, then enhance

---

## Questions for Developer

1. Do you have Kalshi API access?
2. Preferred VPS provider? (DigitalOcean, AWS, etc.)
3. Any specific features beyond the basics?
4. Timeline constraints?

---

**This is a complete blueprint. Follow it step-by-step and you'll have a production Kalshi dashboard in 1 week.**

Good luck! 🚀
