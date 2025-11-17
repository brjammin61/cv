#!/bin/bash

# TradeDeck One-Click Deployment Script
# This script automates as much of the deployment as possible

set -e

echo "🚀 TradeDeck Deployment Wizard"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${BLUE}Creating .env file from template...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env file${NC}"
    echo ""
    echo -e "${RED}⚠️  IMPORTANT: You need to fill in your API keys in .env${NC}"
    echo ""
    echo "Please get your credentials from:"
    echo "  1. Database: https://supabase.com (DATABASE_URL)"
    echo "  2. Stripe: https://stripe.com/dashboard (STRIPE_SECRET_KEY)"
    echo "  3. Cloudinary: https://cloudinary.com/console (CLOUDINARY_*)"
    echo "  4. Pusher: https://dashboard.pusher.com (PUSHER_*)"
    echo "  5. SendGrid: https://sendgrid.com/api_keys (SMTP_PASSWORD)"
    echo ""
    read -p "Press Enter once you've filled in .env..."
fi

# Verify critical env vars
echo -e "${BLUE}Checking environment variables...${NC}"

if ! grep -q "DATABASE_URL=postgresql://" .env; then
    echo -e "${RED}✗ DATABASE_URL not set${NC}"
    exit 1
fi

if ! grep -q "NEXTAUTH_SECRET=" .env || grep -q "NEXTAUTH_SECRET=your-secret" .env; then
    echo -e "${BLUE}Generating NEXTAUTH_SECRET...${NC}"
    SECRET=$(openssl rand -base64 32)
    sed -i "s|NEXTAUTH_SECRET=.*|NEXTAUTH_SECRET=\"$SECRET\"|" .env
    echo -e "${GREEN}✓ Generated NEXTAUTH_SECRET${NC}"
fi

echo -e "${GREEN}✓ Environment variables configured${NC}"
echo ""

# Install dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
npm install
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Setup database
echo -e "${BLUE}Setting up database...${NC}"
npx prisma generate
npx prisma db push
echo -e "${GREEN}✓ Database schema deployed${NC}"
echo ""

# Seed database
echo -e "${BLUE}Seeding initial data...${NC}"
if [ -f prisma/seed.ts ]; then
    npx tsx prisma/seed.ts
    echo -e "${GREEN}✓ Database seeded${NC}"
else
    echo -e "${BLUE}No seed file found, skipping...${NC}"
fi
echo ""

# Build application
echo -e "${BLUE}Building application...${NC}"
npm run build
echo -e "${GREEN}✓ Application built${NC}"
echo ""

# Deploy to Vercel (if CLI installed)
if command -v vercel &> /dev/null; then
    echo -e "${BLUE}Deploying to Vercel...${NC}"
    read -p "Deploy to production now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        vercel --prod
        echo -e "${GREEN}✓ Deployed to Vercel${NC}"
    fi
else
    echo -e "${BLUE}Vercel CLI not found. Install with: npm i -g vercel${NC}"
    echo "Then run: vercel --prod"
fi

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "Next steps:"
echo "1. Configure Stripe webhooks: https://dashboard.stripe.com/webhooks"
echo "2. Add webhook URL: https://yourdomain.com/api/webhooks/stripe"
echo "3. Test a purchase with card: 4242 4242 4242 4242"
echo "4. Start adding listings!"
echo ""
echo "Local dev server: npm run dev"
echo "View database: npx prisma studio"
echo ""
