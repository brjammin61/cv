#!/bin/bash

#########################################################################
# MonadPulse Backend Stop Script
#
# Safely shutdown all services
#########################################################################

set -e

echo "=========================================="
echo "  Stopping MonadPulse Backend"
echo "=========================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if services are running
if ! docker-compose ps | grep -q "Up"; then
    echo -e "${YELLOW}No services appear to be running${NC}"
    exit 0
fi

echo -e "${YELLOW}Stopping all services gracefully...${NC}"
docker-compose down

echo ""
echo -e "${GREEN}All services stopped successfully${NC}"
echo ""
echo "To start again: ./launch.sh"
echo "To remove all data: docker-compose down -v"
echo ""
