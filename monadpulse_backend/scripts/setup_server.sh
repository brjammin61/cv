#!/bin/bash

#############################################################################
# MonadPulse Production Deployment Script
#
# This script sets up a complete production environment for MonadPulse
# Run this on a fresh Ubuntu 20.04+ VPS
#############################################################################

set -e  # Exit on any error

echo "=========================================="
echo "MonadPulse Production Deployment"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 1: Update system packages${NC}"
apt update && apt upgrade -y
echo -e "${GREEN}✓ System updated${NC}"
echo ""

echo -e "${YELLOW}Step 2: Install Docker${NC}"
# Remove old versions
apt remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

# Install dependencies
apt install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker's official GPG key
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Enable Docker to start on boot
systemctl enable docker
systemctl start docker

echo -e "${GREEN}✓ Docker installed${NC}"
echo ""

echo -e "${YELLOW}Step 3: Install Docker Compose${NC}"
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
echo -e "${GREEN}✓ Docker Compose installed${NC}"
echo ""

echo -e "${YELLOW}Step 4: Install Nginx${NC}"
apt install -y nginx
systemctl enable nginx
echo -e "${GREEN}✓ Nginx installed${NC}"
echo ""

echo -e "${YELLOW}Step 5: Install Certbot for SSL${NC}"
apt install -y certbot python3-certbot-nginx
echo -e "${GREEN}✓ Certbot installed${NC}"
echo ""

echo -e "${YELLOW}Step 6: Setup firewall${NC}"
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS
ufw --force enable
echo -e "${GREEN}✓ Firewall configured${NC}"
echo ""

echo -e "${YELLOW}Step 7: Install Git${NC}"
apt install -y git
echo -e "${GREEN}✓ Git installed${NC}"
echo ""

echo -e "${YELLOW}Step 8: Install Node.js (for frontend build)${NC}"
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs
echo -e "${GREEN}✓ Node.js installed${NC}"
echo ""

echo "=========================================="
echo -e "${GREEN}Server Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Clone your repository"
echo "2. Configure environment variables"
echo "3. Run docker-compose up -d"
echo "4. Setup Nginx configuration"
echo "5. Setup SSL certificate"
echo ""
echo "Docker version: $(docker --version)"
echo "Docker Compose version: $(docker-compose --version)"
echo "Node.js version: $(node --version)"
echo "Nginx version: $(nginx -v 2>&1)"
echo ""
