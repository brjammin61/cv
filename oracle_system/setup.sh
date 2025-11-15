#!/bin/bash
# ============================================================================
# THE ORACLE - Setup Script
# ============================================================================

echo "================================"
echo "THE ORACLE - Setup"
echo "================================"
echo ""

# Check Python version
echo "[1/6] Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"

# Create virtual environment
echo ""
echo "[2/6] Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists. Skipping..."
else
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "[3/6] Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"

# Install requirements
echo ""
echo "[4/6] Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Dependencies installed"

# Setup configuration
echo ""
echo "[5/6] Setting up configuration files..."

if [ ! -f "config/api_keys.py" ]; then
    echo "Creating api_keys.py from template..."
    cp config/api_keys.template.py config/api_keys.py
    echo "⚠️  IMPORTANT: Edit config/api_keys.py with your actual API keys!"
else
    echo "api_keys.py already exists. Skipping..."
fi

# Create necessary directories
echo ""
echo "[6/6] Creating necessary directories..."
mkdir -p logs
mkdir -p data
touch logs/.gitkeep
touch data/.gitkeep
echo "✅ Directories created"

# Final instructions
echo ""
echo "================================"
echo "Setup Complete!"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Edit config/api_keys.py with your Kalshi and Polymarket API credentials"
echo "2. Edit config/markets.py to add your specific markets"
echo "3. Run the dashboard: streamlit run oracle_dashboard.py"
echo ""
echo "To activate the virtual environment later:"
echo "  source venv/bin/activate"
echo ""
echo "For help:"
echo "  python oracle_dashboard.py --help"
echo ""
