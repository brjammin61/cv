#!/bin/bash
set -e

echo "=== ORE V2 Dominance Bot - Initial Setup ==="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    exit 1
fi

if ! command -v cargo &> /dev/null; then
    echo -e "${RED}Error: Rust/Cargo is not installed${NC}"
    echo "Install from: https://rustup.rs/"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites check passed${NC}"

# Create wallets directory
echo -e "${YELLOW}Setting up wallets...${NC}"
mkdir -p deployment/wallets

# Generate fresh wallet if it doesn't exist
if [ ! -f "deployment/wallets/bot-wallet.json" ]; then
    echo -e "${YELLOW}Generating fresh wallet...${NC}"
    solana-keygen new --no-bip39-passphrase -o deployment/wallets/bot-wallet.json
    echo -e "${GREEN}✓ Wallet generated${NC}"
    echo -e "${YELLOW}IMPORTANT: Fund this wallet with SOL before running the bot${NC}"
    solana-keygen pubkey deployment/wallets/bot-wallet.json
else
    echo -e "${GREEN}✓ Wallet already exists${NC}"
fi

# Set up environment file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ .env created${NC}"
    echo -e "${YELLOW}IMPORTANT: Edit .env and configure your settings${NC}"
else
    echo -e "${GREEN}✓ .env already exists${NC}"
fi

# Build the project
echo -e "${YELLOW}Building project...${NC}"
cargo build --release

echo -e "${GREEN}✓ Build completed${NC}"

# Set up Redis
echo -e "${YELLOW}Starting Redis...${NC}"
cd deployment/docker
docker-compose up -d redis
cd ../..

echo -e "${GREEN}✓ Redis started${NC}"

echo ""
echo -e "${GREEN}=== Setup Complete ===${NC}"
echo ""
echo "Next steps:"
echo "1. Edit .env with your configuration"
echo "2. Fund your wallet: $(solana-keygen pubkey deployment/wallets/bot-wallet.json)"
echo "3. Run './deployment/scripts/start.sh' to start the bot"
echo ""
