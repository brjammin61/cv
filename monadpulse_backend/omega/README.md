# Omega Engine

**Proprietary MEV Analysis System for MonadPulse**

Omega Engine is the secret weapon that powers MonadPulse's premium tier. It provides:
- Real-time MEV opportunity detection
- Validator efficiency scoring
- Premium analytics API
- Subscription management

---

## ⚠️ IMPORTANT: This is Proprietary Code

- **DO NOT** make this repository public
- **DO NOT** share Omega code or algorithms
- **DO NOT** expose the Omega API publicly without authentication

This is your competitive advantage. Keep it secret.

---

## Quick Start

### 1. Setup Environment

```bash
cd monadpulse_backend/omega
cp .env.example .env
# Edit .env and set:
# - OMEGA_DB_PASSWORD (secure password)
# - MONAD_RPC_URL (Monad RPC endpoint)
```

### 2. Launch Omega Engine

```bash
docker-compose up -d --build
```

This starts:
- Omega Database (PostgreSQL on port 5433)
- Omega Scanner (continuous block scanning)
- Omega API (premium endpoints on port 8001)

### 3. Initialize Database

```bash
# Run once to create tables
docker-compose exec omega-engine python -c "from omega.db_utils import init_omega_database; init_omega_database()"
```

### 4. Verify It's Running

```bash
# Check health
curl http://localhost:8001/omega/health

# Check scanner logs
docker-compose logs -f omega-engine
```

---

## Architecture

```
┌──────────────────────────────────────────┐
│         OMEGA ENGINE (Private)            │
└──────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        ↓                       ↓
┌────────────────┐    ┌──────────────────┐
│ Block Scanner  │    │  Premium API     │
│                │    │  (Port 8001)     │
│ - Detects MEV  │    │                  │
│ - Scores val.  │    │ - Auth required  │
│ - Stores data  │    │ - Rate limited   │
└────────┬───────┘    └────────┬─────────┘
         │                     │
         └─────────┬───────────┘
                   ↓
         ┌──────────────────┐
         │   Omega Database │
         │   (Separate DB)  │
         │   Port 5433      │
         └──────────────────┘
```

---

## Components

### 1. Block Scanner (`scanner.py`)
Scans every Monad block in real-time looking for:
- **Arbitrage** opportunities
- **Liquidations**
- **Sandwich attacks**
- **JIT Liquidity** provision

**Status**: Will activate on Nov 24 when Monad mainnet launches

### 2. MEV Classifier (`classifier.py`)
Scores validators based on:
- MEV captured vs available
- Efficiency trends over time
- Comparison to other validators

**Generates**: Daily efficiency scores, detailed reports, recommendations

### 3. Premium API (`api.py`)
Authenticated API with 3 tiers:
- **BASIC** ($99/mo): Efficiency scores
- **PRO** ($499/mo): Full reports
- **ENTERPRISE** ($2,499/mo): Live MEV opportunities

**Authentication**: API key in `X-API-Key` header

---

## API Endpoints

All endpoints require authentication via API key.

### Get Validator Efficiency

```bash
GET /omega/validator/{address}/efficiency?days=7

curl -H "X-API-Key: your-api-key" \
  http://localhost:8001/omega/validator/0x.../efficiency
```

**Response**:
```json
{
  "validator": "0x...",
  "mev_efficiency": 85.3,
  "timeframe": "7d"
}
```

### Get Detailed Report (PRO+)

```bash
GET /omega/validator/{address}/report

curl -H "X-API-Key: your-api-key" \
  http://localhost:8001/omega/validator/0x.../report
```

**Response**:
```json
{
  "validator": "0x...",
  "efficiency_scores": {
    "24h": 87.2,
    "7d": 85.3,
    "30d": 83.1
  },
  "mev_breakdown": {
    "arbitrage": {"count": 15, "total_profit": 1250.0},
    "liquidation": {"count": 3, "total_profit": 850.0}
  },
  "missed_opportunities": [...],
  "ranking": {"rank": 5, "percentile": 95.2},
  "recommendations": [...]
}
```

### Get Leaderboard

```bash
GET /omega/leaderboard?limit=100&days=7

curl -H "X-API-Key: your-api-key" \
  http://localhost:8001/omega/leaderboard
```

### Get Live MEV Opportunities (ENTERPRISE only)

```bash
GET /omega/opportunities/recent?limit=50

curl -H "X-API-Key: your-api-key" \
  http://localhost:8001/omega/opportunities/recent
```

---

## Managing Subscriptions

### Create New Subscription

```bash
POST /omega/admin/subscribe

curl -X POST http://localhost:8001/omega/admin/subscribe \
  -H "Content-Type: application/json" \
  -d '{
    "validator_address": "0x...",
    "email": "validator@example.com",
    "subscription_tier": "pro"
  }'
```

**Response**:
```json
{
  "validator_address": "0x...",
  "subscription_tier": "pro",
  "api_key": "generated-api-key-here",
  "is_active": true
}
```

**Save this API key** - give it to the customer.

---

## Daily Score Updates

Run this daily via cron to calculate efficiency scores:

```bash
docker-compose exec omega-engine python -c "from omega.classifier import MEVClassifier; MEVClassifier().update_daily_scores()"
```

**Cron job** (add to your VPS):
```bash
# Every day at 1 AM
0 1 * * * cd /opt/monadpulse/monadpulse_backend/omega && docker-compose exec omega-engine python -c "from omega.classifier import MEVClassifier; MEVClassifier().update_daily_scores()"
```

---

## Monitoring

### View Scanner Logs

```bash
docker-compose logs -f omega-engine | grep "OMEGA SCANNER"
```

### View API Logs

```bash
docker-compose logs -f omega-engine | grep "OMEGA API"
```

### Check Database

```bash
docker-compose exec omega-db psql -U trader -d omega_monadpulse

# List tables
\dt

# Check MEV opportunities
SELECT COUNT(*) FROM omega_mev_opportunities;

# Check validator scores
SELECT * FROM omega_validator_scores ORDER BY efficiency_score DESC LIMIT 10;
```

---

## Integration with MonadPulse Public Dashboard

On **Day 31** (after building reputation), add MEV efficiency to the public dashboard:

1. **Update MonadPulse API** to call Omega:

```python
# In monadpulse_backend/api/main.py

from omega.classifier import MEVClassifier

@app.get("/validators/leaderboard")
async def get_leaderboard():
    # ... existing code ...
    
    # Add MEV efficiency from Omega
    classifier = MEVClassifier()
    for validator in validators:
        efficiency = classifier.calculate_mev_efficiency(validator.address)
        validator.mev_efficiency = efficiency
    
    return validators
```

2. **Update React Frontend** to show efficiency column

3. **The Big Reveal**: Everyone sees MEV efficiency, but only premium customers get the details

---

## Security

### Best Practices:

1. **Never expose Omega API publicly**
   - Run on internal port 8001
   - Use firewall rules to restrict access
   - Only expose through your main API with authentication

2. **Rotate API keys regularly**
   - Generate new keys every 90 days
   - Revoke old keys after transition

3. **Encrypt database backups**
   - This data is valuable
   - Competitors would pay for it

4. **Monitor for abuse**
   - Check API usage logs
   - Rate limit aggressively
   - Ban suspicious activity

---

## Troubleshooting

### Scanner not detecting MEV

- Check RPC connection: `curl $MONAD_RPC_URL`
- Check scanner logs: `docker-compose logs omega-engine | grep SCANNER`
- Verify Monad mainnet is live

### API returns 401 Unauthorized

- Check API key is valid
- Verify subscription is active
- Check rate limits not exceeded

### Database connection failed

- Check Omega DB is running: `docker-compose ps omega-db`
- Check password in `.env` matches docker-compose
- Test connection: `docker-compose exec omega-db psql -U trader -d omega_monadpulse`

---

## Revenue Potential

With Omega Engine, you can:

- **Month 3**: $5k MRR (10 BASIC, 3 PRO, 1 ENTERPRISE)
- **Month 6**: $25k MRR (25 BASIC, 15 PRO, 5 ENTERPRISE)
- **Month 12**: $50k MRR (50+ customers)

**This is your Bentley money.** 🚗

---

## Next Steps

1. **Nov 24**: Launch MonadPulse free tier
2. **Days 1-10**: Let scanner collect real data
3. **Days 11-30**: Refine MEV detection with real patterns
4. **Day 31**: Add MEV efficiency to public dashboard
5. **Day 32**: Launch premium tier, start selling

---

**Built for profit. Keep it secret. Ship it.** 🚀
