#!/bin/bash
set -e

echo "=== Starting ORE V2 Dominance Bot ==="

# Load environment
if [ ! -f ".env" ]; then
    echo "Error: .env file not found. Run setup.sh first."
    exit 1
fi

source .env

# Check wallet balance
WALLET_PUBKEY=$(solana-keygen pubkey $WALLET_PATH)
echo "Wallet: $WALLET_PUBKEY"

BALANCE=$(solana balance $WALLET_PUBKEY --url $SOLANA_RPC_URL 2>/dev/null || echo "0")
echo "Balance: $BALANCE"

if [[ "$BALANCE" == "0"* ]]; then
    echo "Warning: Wallet has low/no balance. Fund it before continuing."
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Start services
cd deployment/docker

echo "Starting all services..."
docker-compose up -d

echo ""
echo "=== Bot Started ==="
echo ""
echo "Services:"
echo "  - Bus/Dispatcher: Running"
echo "  - Miner Workers: Running"
echo "  - Redis: Running"
echo "  - Prometheus: http://localhost:9091"
echo "  - Grafana: http://localhost:3000 (admin/admin)"
echo ""
echo "View logs:"
echo "  docker-compose logs -f ore-bus"
echo "  docker-compose logs -f ore-miner-1"
echo ""
echo "Stop all:"
echo "  docker-compose down"
echo ""
