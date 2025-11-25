#!/bin/bash
echo "=== Checking VPS Status ==="
echo ""

echo "1. Current Git Commit:"
cd /opt/monadpulse
git log -1 --oneline

echo ""
echo "2. Testing API Endpoints Locally:"
echo "   - KPI endpoint:"
curl -s http://localhost:8000/stats/kpi | jq . || curl -s http://localhost:8000/stats/kpi
echo ""
echo "   - Validators endpoint:"
curl -s http://localhost:8000/validators/leaderboard | jq . || curl -s http://localhost:8000/validators/leaderboard
echo ""
echo "   - Chart endpoint:"
curl -s http://localhost:8000/stats/chart | jq . || curl -s http://localhost:8000/stats/chart

echo ""
echo "3. Recent API Logs (last 10 lines):"
cd /opt/monadpulse/monadpulse_backend
docker-compose logs --tail=10 api

echo ""
echo "4. API Container Status:"
docker-compose ps api
