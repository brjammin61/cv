#!/bin/bash

# ORE Arbitrage Bot Deployment Script
# This script automates the deployment process

set -e  # Exit on error

echo "🚀 ORE Arbitrage Bot Deployment Script"
echo "======================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ Error: .env file not found${NC}"
    echo "Please copy .env.example to .env and configure it:"
    echo "  cp .env.example .env"
    echo "  nano .env"
    exit 1
fi

echo -e "${GREEN}✅ Configuration file found${NC}"

# Check if wallet exists
WALLET_PATH=$(grep WALLET_PATH .env | cut -d '=' -f2)
if [ -z "$WALLET_PATH" ]; then
    WALLET_PATH="wallet.json"
fi

if [ ! -f "$WALLET_PATH" ]; then
    echo -e "${YELLOW}⚠️  Warning: Wallet file not found at $WALLET_PATH${NC}"
    echo "You'll need to create a wallet before running the bot."
    echo "Run: solana-keygen new --outfile $WALLET_PATH"
fi

# Check deployment method
echo ""
echo "Select deployment method:"
echo "1) Docker (recommended for production)"
echo "2) Local build (for development)"
read -p "Enter choice [1-2]: " choice

case $choice in
    1)
        echo ""
        echo "🐳 Deploying with Docker..."

        # Check if Docker is installed
        if ! command -v docker &> /dev/null; then
            echo -e "${RED}❌ Docker is not installed${NC}"
            exit 1
        fi

        if ! command -v docker-compose &> /dev/null; then
            echo -e "${RED}❌ Docker Compose is not installed${NC}"
            exit 1
        fi

        echo "Building Docker image..."
        docker-compose build

        echo ""
        echo "Starting bot in detached mode..."
        docker-compose up -d

        echo ""
        echo -e "${GREEN}✅ Bot deployed successfully!${NC}"
        echo ""
        echo "View logs with: docker-compose logs -f ore-bot"
        echo "Stop bot with: docker-compose down"
        ;;

    2)
        echo ""
        echo "🔨 Building locally..."

        # Check if Rust is installed
        if ! command -v cargo &> /dev/null; then
            echo -e "${RED}❌ Rust is not installed${NC}"
            echo "Install Rust: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
            exit 1
        fi

        echo "Building in release mode..."
        cargo build --release --bin ore-bot

        echo ""
        echo -e "${GREEN}✅ Build successful!${NC}"
        echo ""
        echo "Run the bot with:"
        echo "  ./target/release/ore-bot"
        echo ""
        echo "Or with logs:"
        echo "  RUST_LOG=info ./target/release/ore-bot"
        ;;

    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo "📝 Important Notes:"
echo "  - Monitor your bot regularly"
echo "  - Start with AUTO_EXECUTE_SWAPS=false for testing"
echo "  - Use a premium RPC endpoint for production"
echo "  - Keep your wallet secure"
echo ""
echo "For help, see README.md or open an issue on GitHub"
