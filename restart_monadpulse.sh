#!/bin/bash
# MonadPulse Quick Restart Script
# Run this on your VPS if services need to be restarted

echo "🔄 Restarting MonadPulse services..."
echo ""

cd /opt/monadpulse/monadpulse_backend

echo "Stopping containers..."
docker-compose down

echo "Starting containers..."
docker-compose up -d

echo ""
echo "✅ Services restarted!"
echo ""
echo "Waiting 10 seconds for services to initialize..."
sleep 10

echo ""
echo "📊 Checking status..."
docker-compose ps

echo ""
echo "📝 Last 20 log lines from ingestor:"
docker-compose logs --tail=20 ingestor

echo ""
echo "✅ Done! Check logs above for Monad connection status."
