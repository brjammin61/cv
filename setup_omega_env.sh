#!/bin/bash
# This script creates the .env file for Omega on the VPS

echo "Creating Omega .env file..."

cat > /opt/monadpulse/monadpulse_backend/omega/.env << 'EOF'
# Omega Engine Configuration

# Database
OMEGA_DB_PASSWORD=omega_secure_prod_2024

# Monad Network
MONAD_RPC_URL=https://rpc.monad.xyz
MONAD_CHAIN_ID=143

# API
OMEGA_API_PORT=8001

# Logging
LOG_LEVEL=INFO
EOF

echo "✅ Omega .env file created"
echo ""
echo "Configured with:"
echo "  - Monad RPC: https://rpc.monad.xyz"
echo "  - Chain ID: 143"
echo "  - API Port: 8001"
echo "  - Database Port: 5433"
echo ""
