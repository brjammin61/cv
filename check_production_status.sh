#!/bin/bash
# MonadPulse Production Status Check Script
# Run this on your VPS at 143.110.144.231

echo "========================================"
echo "MONADPULSE PRODUCTION STATUS CHECK"
echo "========================================"
echo ""

echo "1. CHECKING DOCKER CONTAINERS..."
echo "---"
docker-compose -f /opt/monadpulse/monadpulse_backend/docker-compose.yml ps
echo ""

echo "2. CHECKING MONAD CONNECTION (Last 10 log lines)..."
echo "---"
docker-compose -f /opt/monadpulse/monadpulse_backend/docker-compose.yml logs --tail=10 ingestor | grep -E "(Connected to Monad|Real blockchain metrics|TPS|Block:)"
echo ""

echo "3. CHECKING API HEALTH..."
echo "---"
curl -s http://localhost:8000/api/validators | head -c 200
echo ""
echo ""

echo "4. CHECKING FRONTEND..."
echo "---"
curl -s -I http://localhost/ | head -5
echo ""

echo "5. CHECKING DISK SPACE..."
echo "---"
df -h / | tail -1
echo ""

echo "6. CHECKING MEMORY..."
echo "---"
free -h | grep Mem
echo ""

echo "7. CHECKING LATEST MONAD BLOCK..."
echo "---"
docker-compose -f /opt/monadpulse/monadpulse_backend/docker-compose.yml logs --tail=5 ingestor | grep "Block:" | tail -1
echo ""

echo "========================================"
echo "STATUS CHECK COMPLETE"
echo "========================================"
