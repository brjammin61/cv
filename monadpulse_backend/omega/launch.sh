#!/bin/bash

echo "========================================"
echo "  Omega Engine - Launch Script"
echo "========================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "✅ Created .env - PLEASE EDIT IT WITH YOUR SETTINGS"
    echo ""
    exit 1
fi

echo "🚀 Starting Omega Engine..."
echo ""

# Build and start services
docker-compose up -d --build

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Initialize database
echo ""
echo "🗄️  Initializing Omega database..."
docker-compose exec -T omega-engine python -c "from omega.db_utils import init_omega_database; init_omega_database()"

echo ""
echo "========================================"
echo "✅ Omega Engine is running!"
echo "========================================"
echo ""
echo "📊 API: http://localhost:8001/omega/docs"
echo "🗄️  Database: localhost:5433"
echo ""
echo "View logs:"
echo "  docker-compose logs -f omega-engine"
echo ""
echo "Stop:"
echo "  docker-compose down"
echo ""
