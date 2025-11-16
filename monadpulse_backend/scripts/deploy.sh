#!/bin/bash

#############################################################################
# MonadPulse One-Command Deployment
#
# This script deploys the complete MonadPulse system to production
# Run this AFTER setup_server.sh has completed
#############################################################################

set -e

echo "=========================================="
echo "MonadPulse Deployment Script"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
APP_DIR="/opt/monadpulse"
REPO_URL="https://github.com/brjammin61/cv.git"  # Update this!
DOMAIN_API="api.monadpulse.io"  # Update this!
DOMAIN_FRONTEND="monadpulse.io"  # Update this!

echo -e "${YELLOW}Step 1: Clone/update repository${NC}"
if [ -d "$APP_DIR" ]; then
    echo "Repository exists, pulling latest changes..."
    cd $APP_DIR
    git pull
else
    echo "Cloning repository..."
    git clone $REPO_URL $APP_DIR
    cd $APP_DIR
fi
echo -e "${GREEN}✓ Repository ready${NC}"
echo ""

echo -e "${YELLOW}Step 2: Setup backend environment${NC}"
cd $APP_DIR/monadpulse_backend

# Create production .env if doesn't exist
if [ ! -f .env ]; then
    echo "Creating production .env file..."
    cat > .env << EOF
# Database Configuration
POSTGRES_PASSWORD=$(openssl rand -base64 32)

# Application Configuration
LOG_LEVEL=WARNING

# Ingestor Configuration
UPDATE_INTERVAL_SECONDS=120

# Monad Network (update when SDK available)
# MONAD_RPC_URL=https://rpc.monad.xyz
EOF
    echo -e "${GREEN}✓ Created .env file${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi
echo ""

echo -e "${YELLOW}Step 3: Deploy backend with Docker Compose${NC}"
docker-compose down 2>/dev/null || true
docker-compose up -d --build
echo -e "${GREEN}✓ Backend deployed${NC}"
echo ""

echo -e "${YELLOW}Step 4: Build frontend${NC}"
cd $APP_DIR/monadpulse_frontend

# Update API URL for production
cat > src/config.js << EOF
export const API_BASE_URL = 'https://${DOMAIN_API}';
EOF

# Install dependencies and build
npm install --production
npm run build
echo -e "${GREEN}✓ Frontend built${NC}"
echo ""

echo -e "${YELLOW}Step 5: Deploy frontend to web root${NC}"
rm -rf /var/www/monadpulse
mkdir -p /var/www/monadpulse
cp -r build/* /var/www/monadpulse/
chown -R www-data:www-data /var/www/monadpulse
echo -e "${GREEN}✓ Frontend deployed${NC}"
echo ""

echo -e "${YELLOW}Step 6: Setup Nginx configuration${NC}"
cp $APP_DIR/monadpulse_backend/scripts/nginx_config.conf /etc/nginx/sites-available/monadpulse

# Update domains in config
sed -i "s/api.monadpulse.io/$DOMAIN_API/g" /etc/nginx/sites-available/monadpulse
sed -i "s/monadpulse.io/$DOMAIN_FRONTEND/g" /etc/nginx/sites-available/monadpulse

# Enable site
ln -sf /etc/nginx/sites-available/monadpulse /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
echo -e "${GREEN}✓ Nginx configured${NC}"
echo ""

echo "=========================================="
echo -e "${GREEN}Deployment Complete!${NC}"
echo "=========================================="
echo ""
echo "Your MonadPulse system is now running:"
echo ""
echo "Backend API:  http://$DOMAIN_API"
echo "Frontend:     http://$DOMAIN_FRONTEND"
echo ""
echo "Next steps:"
echo "1. Point your domains to this server's IP"
echo "2. Setup SSL: sudo certbot --nginx -d $DOMAIN_API -d $DOMAIN_FRONTEND"
echo "3. Test the deployment"
echo ""
echo "Useful commands:"
echo "  View backend logs:  docker-compose logs -f"
echo "  Restart backend:    docker-compose restart"
echo "  Stop backend:       docker-compose down"
echo ""
