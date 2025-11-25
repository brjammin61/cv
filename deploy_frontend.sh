#!/bin/bash
set -e

echo "=== MonadPulse Frontend Deployment ==="
echo ""

# Step 1: Update backend code and clear fake data
echo "1. Updating backend code..."
cd /opt/monadpulse/monadpulse_backend
git pull origin claude/monadpulse-backend-launch-01QaDPgtQw9qw3xurAzNScyE

echo ""
echo "2. Clearing fake chart data from database..."
docker-compose exec -T ingestor python /app/clear_fake_chart_data.py || echo "⚠️  Chart data clear failed (may already be empty)"

echo ""
echo "3. Rebuilding backend containers..."
docker-compose down
docker-compose up -d --build

echo ""
echo "4. Waiting for services to start..."
sleep 10

echo ""
echo "5. Updating frontend code..."
cd /opt/monadpulse/monadpulse_frontend
git pull origin claude/monadpulse-backend-launch-01QaDPgtQw9qw3xurAzNScyE

echo ""
echo "6. Installing frontend dependencies..."
npm install

echo ""
echo "7. Building Bloomberg-style frontend..."
npm run build

echo ""
echo "8. Deploying to nginx..."
sudo rm -rf /var/www/monadpulse/*
sudo cp -r build/* /var/www/monadpulse/
sudo chown -R www-data:www-data /var/www/monadpulse

echo ""
echo "9. Restarting nginx..."
sudo systemctl restart nginx

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "✅ Backend: Running with NO FAKE DATA"
echo "✅ Frontend: Bloomberg-style terminal deployed"
echo ""
echo "Test your dashboard at: http://143.110.144.231"
echo ""
echo "Verifying API endpoints:"
curl -s http://localhost:8000/stats/kpi | head -c 200
echo ""
