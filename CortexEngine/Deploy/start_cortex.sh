#!/bin/bash
# ============================================================
# THE CORTEX PROTOCOL - STARTUP SCRIPT (Linux/Mac)
# ============================================================

echo ""
echo "==============================================="
echo "   THE CORTEX PROTOCOL - STARTING ENGINE"
echo "==============================================="
echo ""

# Navigate to Python directory
cd "$(dirname "$0")/../Python"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "[1/3] Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "[2/3] Installing dependencies..."
    pip install -r requirements.txt
else
    echo "[1/3] Activating virtual environment..."
    source venv/bin/activate
fi

echo "[3/3] Starting Cortex Brain..."
echo ""
echo "==============================================="
echo "   CORTEX ONLINE - WAITING FOR NINJATRADER"
echo "==============================================="
echo ""

python cortex_server.py
