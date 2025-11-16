#!/bin/bash

#########################################################################
# MonadPulse Backend Launch Script
#
# Production-ready launch script with health checks and validation
#########################################################################

set -e  # Exit on error

echo "=========================================="
echo "  MonadPulse Backend Launch Script"
echo "=========================================="
echo ""

# Color codes for pretty output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# =============================================================================
# Pre-flight Checks
# =============================================================================

echo -e "${YELLOW}Running pre-flight checks...${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi
echo -e "${GREEN}✓ Docker installed${NC}"

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    echo "Install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose installed${NC}"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Warning: .env file not found${NC}"
    echo "Creating .env from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}✓ Created .env file${NC}"
        echo -e "${YELLOW}Please review and update .env with your configuration${NC}"
    else
        echo -e "${RED}Error: .env.example not found${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}✓ Configuration file exists${NC}"

# Check if ports are available
echo -e "${YELLOW}Checking port availability...${NC}"

if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${RED}Error: Port 8000 is already in use${NC}"
    echo "Stop the service using port 8000 or update docker-compose.yml"
    exit 1
fi
echo -e "${GREEN}✓ Port 8000 available${NC}"

if lsof -Pi :5432 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}Warning: Port 5432 is in use (another PostgreSQL?)${NC}"
    echo "This may cause conflicts. Consider stopping it or changing the port."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}All pre-flight checks passed!${NC}"
echo ""

# =============================================================================
# Build and Launch
# =============================================================================

echo -e "${YELLOW}Building Docker containers...${NC}"
docker-compose build

echo ""
echo -e "${YELLOW}Starting services...${NC}"
docker-compose up -d

echo ""
echo -e "${YELLOW}Waiting for services to be healthy...${NC}"

# Wait for database to be healthy
MAX_WAIT=60
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if docker-compose ps db | grep -q "healthy"; then
        echo -e "${GREEN}✓ Database is healthy${NC}"
        break
    fi
    echo -n "."
    sleep 2
    WAITED=$((WAITED + 2))
done

if [ $WAITED -ge $MAX_WAIT ]; then
    echo -e "${RED}Error: Database failed to become healthy${NC}"
    echo "Check logs: docker-compose logs db"
    exit 1
fi

# Wait for API to be healthy
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ API is healthy${NC}"
        break
    fi
    echo -n "."
    sleep 2
    WAITED=$((WAITED + 2))
done

if [ $WAITED -ge $MAX_WAIT ]; then
    echo -e "${RED}Error: API failed to become healthy${NC}"
    echo "Check logs: docker-compose logs api"
    exit 1
fi

# Check ingestor
sleep 5
if docker-compose ps ingestor | grep -q "Up"; then
    echo -e "${GREEN}✓ Ingestor is running${NC}"
else
    echo -e "${RED}Error: Ingestor is not running${NC}"
    echo "Check logs: docker-compose logs ingestor"
    exit 1
fi

# =============================================================================
# Success!
# =============================================================================

echo ""
echo "=========================================="
echo -e "${GREEN}  MonadPulse Backend Launched!${NC}"
echo "=========================================="
echo ""
echo "Services:"
echo "  • API:       http://localhost:8000"
echo "  • API Docs:  http://localhost:8000/docs"
echo "  • Database:  postgresql://trader:***@localhost:5432/monadpulse"
echo ""
echo "Quick commands:"
echo "  • View logs:        docker-compose logs -f"
echo "  • View API logs:    docker-compose logs -f api"
echo "  • View ingestor:    docker-compose logs -f ingestor"
echo "  • Stop services:    docker-compose down"
echo "  • Restart:          docker-compose restart"
echo ""
echo "Testing the API:"
echo "  curl http://localhost:8000/health"
echo "  curl http://localhost:8000/stats/kpi"
echo "  curl http://localhost:8000/validators/leaderboard"
echo ""
echo -e "${GREEN}Ready to integrate with your React frontend!${NC}"
echo ""
