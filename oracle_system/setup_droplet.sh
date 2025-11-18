#!/bin/bash
# The Oracle - DigitalOcean Droplet Setup Script
# Automates complete deployment of The Oracle system

set -e  # Exit on error

echo "================================="
echo "🔮 THE ORACLE - DROPLET SETUP"
echo "================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Installation directory
INSTALL_DIR="/opt/oracle"

echo -e "${BLUE}[1/8] Updating system packages...${NC}"
apt-get update -qq
apt-get upgrade -y -qq

echo -e "${BLUE}[2/8] Installing dependencies...${NC}"
apt-get install -y -qq \
    python3 \
    python3-pip \
    git \
    curl \
    sqlite3 \
    ufw

echo -e "${BLUE}[3/8] Cloning Oracle repository...${NC}"
if [ -d "$INSTALL_DIR" ]; then
    echo "Oracle directory exists, pulling latest..."
    cd $INSTALL_DIR
    git pull
else
    git clone https://github.com/brjammin61/cv.git $INSTALL_DIR
    cd $INSTALL_DIR
    git checkout claude/build-feature-01Am47fqpC7CFtcVXLJ7VUDb
fi

cd $INSTALL_DIR/oracle_system

echo -e "${BLUE}[4/8] Installing Python dependencies...${NC}"
pip3 install --quiet --upgrade pip
pip3 install --quiet -r requirements.txt
pip3 install --quiet flask

echo -e "${BLUE}[5/8] Creating directories...${NC}"
mkdir -p data
mkdir -p logs
mkdir -p /root/.kalshi

echo -e "${BLUE}[6/8] Configuring API keys...${NC}"
echo ""
echo -e "${YELLOW}Please enter your Kalshi API credentials:${NC}"
echo ""

# Prompt for API key
read -p "Kalshi API Key: " KALSHI_API_KEY

# Check if private key file exists
PRIVATE_KEY_PATH="/root/.kalshi/private_key.pem"
if [ ! -f "$PRIVATE_KEY_PATH" ]; then
    echo ""
    echo -e "${YELLOW}Private key not found at $PRIVATE_KEY_PATH${NC}"
    echo "Please upload your private_key.pem file first:"
    echo ""
    echo "  From your Mac, run:"
    echo "  scp /path/to/private_key.pem root@$(curl -s ifconfig.me):/root/.kalshi/"
    echo ""
    read -p "Press Enter once you've uploaded the file..."
fi

# Update config/api_keys.py
cat > config/api_keys.py <<EOF
"""
API Keys Configuration
IMPORTANT: Keep this file secure and never commit to git!
"""

# Kalshi API Configuration
KALSHI_API_KEY = "$KALSHI_API_KEY"
KALSHI_PRIVATE_KEY_PATH = "$PRIVATE_KEY_PATH"
KALSHI_API_BASE = "https://api.elections.kalshi.com/trade-api/v2"

# Demo/Test Configuration
KALSHI_DEMO_API_BASE = "https://demo-api.kalshi.co/trade-api/v2"
EOF

chmod 600 config/api_keys.py

echo -e "${GREEN}✓ API keys configured${NC}"

echo -e "${BLUE}[7/8] Setting up systemd services...${NC}"

# Create Oracle service
cat > /etc/systemd/system/oracle.service <<EOF
[Unit]
Description=The Oracle - Automated Prediction Market Trading System
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR/oracle_system
ExecStart=/usr/bin/python3 $INSTALL_DIR/oracle_system/run_oracle_system.py --mode paper
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Create Dashboard service
cat > /etc/systemd/system/oracle-dashboard.service <<EOF
[Unit]
Description=The Oracle - Web Dashboard
After=network.target oracle.service

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR/oracle_system
ExecStart=/usr/bin/python3 $INSTALL_DIR/oracle_system/web_dashboard.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
systemctl daemon-reload

# Enable services (start on boot)
systemctl enable oracle
systemctl enable oracle-dashboard

echo -e "${GREEN}✓ Systemd services created${NC}"

echo -e "${BLUE}[8/8] Configuring firewall...${NC}"
ufw --force enable
ufw allow 22/tcp    # SSH
ufw allow 8080/tcp  # Dashboard

echo -e "${GREEN}✓ Firewall configured${NC}"

echo ""
echo "================================="
echo -e "${GREEN}🎉 SETUP COMPLETE!${NC}"
echo "================================="
echo ""
echo "Starting services..."
systemctl start oracle
systemctl start oracle-dashboard

sleep 3

echo ""
echo "Service Status:"
systemctl status oracle --no-pager -l | head -n 5
echo ""
systemctl status oracle-dashboard --no-pager -l | head -n 5

echo ""
echo "================================="
echo -e "${GREEN}✅ The Oracle is now running!${NC}"
echo "================================="
echo ""
echo "📊 Access your dashboard at:"
echo ""
PUBLIC_IP=$(curl -s ifconfig.me || curl -s icanhazip.com || echo "YOUR_SERVER_IP")
echo -e "${YELLOW}   → http://$PUBLIC_IP:8080${NC}"
echo ""
echo "🎮 Management Commands:"
echo ""
echo "  Check status:    systemctl status oracle"
echo "  View logs:       journalctl -u oracle -f"
echo "  Restart:         systemctl restart oracle"
echo "  Stop:            systemctl stop oracle"
echo ""
echo "📁 Installation directory: $INSTALL_DIR/oracle_system"
echo ""
echo "🔮 The Oracle will now run 24/7 and auto-start on reboot!"
echo ""
echo "================================="
