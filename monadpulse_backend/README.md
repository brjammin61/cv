# MonadPulse Backend

**Production-Ready Validator Analytics and MEV Tracking for Monad Mainnet**

MonadPulse is a professional-grade analytics dashboard for the Monad blockchain ecosystem. This backend provides real-time validator performance metrics, MEV efficiency tracking, and network statistics.

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose installed
- 4GB+ RAM available
- Port 8000 and 5432 available

### Launch in 3 Commands

```bash
cd monadpulse_backend
cp .env.example .env  # Edit if needed
docker-compose up --build
```

**Your API is now live at:** `http://localhost:8000`

**Interactive API docs:** `http://localhost:8000/docs`

---

## 📊 Architecture Overview

```
┌─────────────────┐
│  React Frontend │ (Your existing code)
│  (Port 3000)    │
└────────┬────────┘
         │ HTTP
         ↓
┌─────────────────┐
│   FastAPI       │ (This repository)
│   (Port 8000)   │
└────────┬────────┘
         │ SQL
         ↓
┌─────────────────┐      ┌──────────────┐
│  PostgreSQL DB  │ ←────┤  Ingestor    │
│  (Port 5432)    │      │  Service     │
└─────────────────┘      └──────────────┘
                              │
                              ↓
                    ┌──────────────────┐
                    │ Monad SDK        │
                    │ (Future: Real    │
                    │  blockchain data)│
                    └──────────────────┘
```

### Services

1. **API (`monadpulse-api`)**: FastAPI server serving REST endpoints for the React frontend
2. **Ingestor (`monadpulse-ingestor`)**: Background service fetching and processing validator data
3. **Database (`monadpulse-db`)**: PostgreSQL database storing all analytics data

---

## 🔌 API Endpoints

### Health Check
```
GET /health
```
Returns service health status and database connectivity.

### Dashboard KPIs
```
GET /stats/kpi
```
Returns:
- Total MEV captured (14 days)
- MEV change percentage
- Network TPS (24h average)
- Top validator name and Omega partner status
- Average MEV efficiency

### Chart Data
```
GET /stats/chart
```
Returns 14 days of historical MEV data for charting.

### Validator Leaderboard
```
GET /validators/leaderboard?limit=100
```
Returns validators ranked by MEV efficiency.

### Individual Validator
```
GET /validators/{validator_name}
```
Returns detailed metrics for a specific validator.

---

## 🛠️ Development Setup

### Local Development (Without Docker)

1. **Setup Python Environment**
```bash
cd api
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Start PostgreSQL**
```bash
docker run -d \
  --name monadpulse-db \
  -e POSTGRES_USER=trader \
  -e POSTGRES_PASSWORD=your_secret_password \
  -e POSTGRES_DB=monadpulse \
  -p 5432:5432 \
  postgres:14-alpine
```

3. **Run API Server**
```bash
cd api
export DATABASE_URL="postgresql://trader:your_secret_password@localhost/monadpulse"
uvicorn main:app --reload
```

4. **Run Ingestor (in separate terminal)**
```bash
cd ingestor
export DATABASE_URL="postgresql://trader:your_secret_password@localhost/monadpulse"
python ingestor.py
```

### Testing the API

```bash
# Health check
curl http://localhost:8000/health

# Get KPI stats
curl http://localhost:8000/stats/kpi

# Get chart data
curl http://localhost:8000/stats/chart

# Get leaderboard
curl http://localhost:8000/validators/leaderboard
```

---

## 🔐 Environment Variables

Create a `.env` file in the root directory:

```env
# Database
POSTGRES_PASSWORD=your_secure_password_here

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR

# Ingestor
UPDATE_INTERVAL_SECONDS=60  # How often to fetch new data
```

---

## 🚢 Production Deployment

### AWS / DigitalOcean / Any VPS

1. **Setup Server**
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

2. **Clone and Configure**
```bash
git clone <your-repo>
cd monadpulse_backend
nano .env  # Set production password!
```

3. **Launch**
```bash
docker-compose up -d
```

4. **Setup Nginx Reverse Proxy (Recommended)**
```nginx
server {
    listen 80;
    server_name api.monadpulse.io;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

5. **Setup SSL with Let's Encrypt**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d api.monadpulse.io
```

### Monitoring

```bash
# View logs
docker-compose logs -f

# View specific service
docker-compose logs -f api
docker-compose logs -f ingestor

# Check status
docker-compose ps
```

---

## 📈 Integrating Real Monad Data

**IMPORTANT**: This system currently uses MOCK DATA for rapid development and launch.

To integrate real Monad blockchain data:

1. **Install Monad SDK** (when available)
```bash
# Add to ingestor/requirements.txt
monad-sdk>=1.0.0
```

2. **Update `ingestor/ingestor.py`**

Replace the `fetch_validator_data()` function:

```python
from monad_sdk import MonadClient

def fetch_validator_data():
    client = MonadClient(rpc_url=os.environ['MONAD_RPC_URL'])

    validators = []
    raw_validators = client.staking.get_validators()

    for val in raw_validators:
        validators.append({
            "name": val.moniker,
            "address": val.operator_address,
            "uptime_pct": val.uptime_percentage,
            "apy_pct": calculate_apy(val),
            "mev_efficiency": calculate_mev_efficiency(val),
            "is_omega_partner": val.operator_address in OMEGA_PARTNERS,
            "blocks_produced": val.blocks_proposed
        })

    return validators
```

3. **Add RPC URL to `.env`**
```env
MONAD_RPC_URL=https://rpc.monad.xyz
```

---

## 🔍 Database Schema

### `validators` Table
- `id`: Primary key
- `rank`: Validator rank by MEV efficiency
- `name`: Validator name
- `address`: Blockchain address
- `uptime_pct`: Uptime percentage
- `apy_pct`: Annual percentage yield
- `mev_efficiency`: MEV efficiency score
- `is_omega_partner`: Boolean flag for Omega Engine partners
- `blocks_produced`: Number of blocks produced
- `last_updated`: Last update timestamp

### `chart_data` Table
- `id`: Primary key
- `timestamp`: Data point timestamp
- `name`: Display label (e.g., "11/14")
- `mev_captured_usd`: MEV value in USD

### `network_stats` Table
- `id`: Primary key
- `timestamp`: Record timestamp
- `total_mev`: Total MEV captured
- `network_tps`: Network transactions per second
- `avg_mev_efficiency`: Average MEV efficiency
- `mev_change_pct`: MEV change percentage

---

## 🐛 Troubleshooting

### "Connection refused" from React app
- Ensure API is running: `docker-compose ps`
- Check CORS settings in `api/main.py`
- Verify React app is calling `http://localhost:8000`

### "No validator data available"
- Wait 60 seconds for first ingestor cycle
- Check ingestor logs: `docker-compose logs ingestor`
- Verify database connection: `docker-compose logs db`

### Database connection errors
- Ensure PostgreSQL is healthy: `docker-compose ps db`
- Check credentials in `.env` match `docker-compose.yml`

### Port conflicts
- Change ports in `docker-compose.yml` if 8000 or 5432 are taken
- Update React app API URL accordingly

---

## 📝 Next Steps

1. **Frontend Integration**: Your React app should call `http://localhost:8000`
2. **Real Data**: Integrate Monad SDK when mainnet launches
3. **Omega Engine**: Build the private MEV scanner to populate `mev_efficiency` scores
4. **Analytics**: Add more sophisticated metrics and historical tracking
5. **Alerting**: Add Telegram/Discord webhooks for critical events

---

## 🤝 Strategic Positioning

### The MonadPulse 2-Track Plan

**Track 1 (Public)**: MonadPulse Dashboard
- Free analytics for the community
- Builds reputation and user base
- Proves technical capability

**Track 2 (Private)**: Omega Engine
- Private MEV scanner
- Powers the "Omega Validator" in leaderboard
- Demonstrates superior MEV efficiency

### Day 1-30 Launch Strategy

**Days 1-10**: Deploy MonadPulse with public validator data
**Days 11-30**: Deploy Omega Engine, MEV efficiency becomes your moat
**Day 31**: Approach Monad Foundation with proven ecosystem value

---

## 📧 Support

For issues or questions:
- Check `/docs` endpoint for API documentation
- Review logs: `docker-compose logs -f`
- Inspect database: `psql postgresql://trader:password@localhost/monadpulse`

---

## ⚖️ License

Proprietary - All Rights Reserved

---

**Built for the Monad mainnet launch. Ready to dominate the validator analytics space.**

🚀 **Let's capture that Bentley money.**
