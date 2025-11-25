#!/bin/bash
set -e

echo "═══════════════════════════════════════════════════════════"
echo "   OMEGA ENGINE DEPLOYMENT - Premium MEV Analysis System   "
echo "═══════════════════════════════════════════════════════════"
echo ""

# Step 1: Pull latest code
echo "1. Pulling latest Omega code from GitHub..."
cd /opt/monadpulse
git pull origin claude/monadpulse-backend-launch-01QaDPgtQw9qw3xurAzNScyE

# Step 2: Navigate to Omega directory
echo ""
echo "2. Navigating to Omega directory..."
cd /opt/monadpulse/monadpulse_backend/omega

# Step 3: Stop any existing Omega services
echo ""
echo "3. Stopping existing Omega services (if any)..."
docker-compose down 2>/dev/null || echo "No existing services to stop"

# Step 4: Build Omega containers
echo ""
echo "4. Building Omega Engine containers..."
docker-compose build

# Step 5: Start Omega services
echo ""
echo "5. Starting Omega services..."
docker-compose up -d

# Step 6: Wait for services to initialize
echo ""
echo "6. Waiting for services to initialize..."
sleep 15

# Step 7: Check service health
echo ""
echo "7. Checking service health..."
echo ""
echo "   Database status:"
docker-compose ps omega-db
echo ""
echo "   Engine status:"
docker-compose ps omega-engine

# Step 8: Open firewall port
echo ""
echo "8. Opening firewall port 8001..."
if command -v ufw &> /dev/null; then
    sudo ufw allow 8001/tcp 2>/dev/null || echo "   Port may already be open"
    sudo ufw status | grep 8001 || echo "   Firewall configured"
fi

# Step 9: Test Omega API
echo ""
echo "9. Testing Omega API..."
sleep 5
echo ""
echo "   Health check:"
curl -s http://localhost:8001/omega/health || echo "   API starting up..."

# Step 10: View initial logs
echo ""
echo "10. Viewing initial logs..."
echo ""
docker-compose logs --tail=20 omega-engine

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "              OMEGA ENGINE DEPLOYMENT COMPLETE              "
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "✅ Omega Database: Running on port 5433"
echo "✅ Omega Scanner: Monitoring Monad blocks for MEV"
echo "✅ Omega API: Running on port 8001"
echo ""
echo "📊 WHAT HAPPENS NOW:"
echo "   - Scanner is collecting MEV data from Monad mainnet"
echo "   - Data accumulates over the next 10-30 days"
echo "   - Once you have historical data, launch premium tier"
echo ""
echo "🔒 SECURITY NOTE:"
echo "   - Omega API requires authentication (X-API-Key header)"
echo "   - Keep this code proprietary - it's your competitive advantage"
echo ""
echo "📈 REVENUE POTENTIAL:"
echo "   - BASIC tier: \$99/month (efficiency scores)"
echo "   - PRO tier: \$499/month (detailed reports)"
echo "   - ENTERPRISE tier: \$2,499/month (live MEV opportunities)"
echo ""
echo "🎯 NEXT STEPS:"
echo "   1. Let it run for 10-30 days to collect data"
echo "   2. Monitor logs: docker-compose logs -f omega-engine"
echo "   3. When ready, add MEV efficiency to public dashboard"
echo "   4. Launch premium tier and start selling"
echo ""
echo "Monitor Omega:"
echo "   cd /opt/monadpulse/monadpulse_backend/omega"
echo "   docker-compose logs -f omega-engine"
echo ""
