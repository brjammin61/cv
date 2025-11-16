#!/bin/bash

# Simple start script for ORE Arbitrage Bot

set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Set default log level if not set
if [ -z "$RUST_LOG" ]; then
    export RUST_LOG=info
fi

echo "🤖 Starting ORE Arbitrage Bot..."
echo "Log level: $RUST_LOG"
echo ""

# Check if binary exists
if [ ! -f ./target/release/ore-bot ]; then
    echo "Binary not found. Building..."
    cargo build --release --bin ore-bot
fi

# Run the bot
./target/release/ore-bot
