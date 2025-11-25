#!/bin/bash
# MIMIC V3.1 Deployment Script
# Run this on your DigitalOcean droplet after cloning the repo

set -e  # Exit on error

echo "=========================================="
echo "  MIMIC V3.1 Deployment Script"
echo "=========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root (sudo ./deploy.sh)${NC}"
    exit 1
fi

INSTALL_DIR="/root/mimic_v3"

# Step 1: System Updates
echo -e "${YELLOW}[1/7] Updating system...${NC}"
apt update && apt upgrade -y

# Step 2: Install Python
echo -e "${YELLOW}[2/7] Installing Python...${NC}"
apt install -y python3 python3-pip python3-venv git curl

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Python version: $PYTHON_VERSION"

# Step 3: Create directory structure
echo -e "${YELLOW}[3/7] Setting up directories...${NC}"
mkdir -p $INSTALL_DIR/logs
mkdir -p $INSTALL_DIR/models
mkdir -p $INSTALL_DIR/config

# Copy files if not already in place
if [ ! -f "$INSTALL_DIR/main_mimic.py" ]; then
    echo "Copying files to $INSTALL_DIR..."
    cp -r . $INSTALL_DIR/
fi

cd $INSTALL_DIR

# Step 4: Create virtual environment
echo -e "${YELLOW}[4/7] Creating Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# Step 5: Install dependencies
echo -e "${YELLOW}[5/7] Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Step 6: Set up environment file
echo -e "${YELLOW}[6/7] Setting up environment...${NC}"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${YELLOW}IMPORTANT: Edit .env with your API keys!${NC}"
    echo "  nano $INSTALL_DIR/.env"
fi

# Step 7: Install systemd service
echo -e "${YELLOW}[7/7] Installing systemd service...${NC}"
cp config/mimic.service /etc/systemd/system/mimic.service
systemctl daemon-reload
systemctl enable mimic

echo ""
echo -e "${GREEN}=========================================="
echo "  Deployment Complete!"
echo "==========================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Edit your API keys:"
echo "     nano $INSTALL_DIR/.env"
echo ""
echo "  2. Test the system (paper trading):"
echo "     cd $INSTALL_DIR && source venv/bin/activate"
echo "     python main_mimic.py --demo"
echo ""
echo "  3. Start the service:"
echo "     systemctl start mimic"
echo ""
echo "  4. Monitor logs:"
echo "     journalctl -u mimic -f"
echo "     tail -f $INSTALL_DIR/logs/mimic_cortex.log"
echo ""
echo "  5. Check status:"
echo "     systemctl status mimic"
echo ""
echo -e "${YELLOW}WARNING: Start with --demo and paper trading first!${NC}"
echo ""
