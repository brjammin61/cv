# MonadPulse - Quick Start Guide

Get MonadPulse running in **under 5 minutes**.

---

## Prerequisites

- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- Docker Compose installed ([Get Docker Compose](https://docs.docker.com/compose/install/))
- Port 8000 available

---

## 🚀 Launch in 3 Commands

```bash
cd monadpulse_backend
cp .env.example .env
./launch.sh
```

**That's it!** Your API is now running at `http://localhost:8000`

---

## ✅ Verify It's Working

Open your browser or use curl:

```bash
# Health check
curl http://localhost:8000/health

# Get dashboard stats
curl http://localhost:8000/stats/kpi

# Get chart data
curl http://localhost:8000/stats/chart

# Get validator leaderboard
curl http://localhost:8000/validators/leaderboard
```

Or visit the **interactive API docs**: `http://localhost:8000/docs`

---

## 🔗 Connect Your React Frontend

Update your React app's API URL to:

```javascript
const API_BASE_URL = 'http://localhost:8000';
```

Your React app will now fetch live data from the MonadPulse backend!

---

## 📊 View Logs

```bash
# All services
docker-compose logs -f

# Just the API
docker-compose logs -f api

# Just the ingestor
docker-compose logs -f ingestor
```

---

## 🛑 Stop Services

```bash
./stop.sh

# Or manually
docker-compose down
```

---

## 🔧 Troubleshooting

### "Port 8000 is already in use"

Find and kill the process:
```bash
# On Mac/Linux
lsof -ti:8000 | xargs kill -9

# On Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### "Database connection failed"

Wait 30 seconds for the database to initialize, then:
```bash
docker-compose restart api ingestor
```

### "No data showing in dashboard"

The ingestor runs every 60 seconds. Wait 1 minute after startup for data to appear.

Check ingestor logs:
```bash
docker-compose logs ingestor
```

---

## 🎯 Next Steps

1. ✅ Backend is running
2. 🔗 Connect your React frontend
3. 📈 View live validator data in your dashboard
4. 🚀 Deploy to production (see `DEPLOYMENT.md`)

---

## 🆘 Need Help?

- **API Documentation**: `http://localhost:8000/docs`
- **Full README**: See `README.md`
- **Production Deployment**: See `DEPLOYMENT.md`

---

**You're ready to launch MonadPulse!**

🚀 Let's capture that Monad mainnet traffic.
