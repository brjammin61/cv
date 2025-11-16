#!/bin/bash
set -e

echo "=== Stopping ORE V2 Dominance Bot ==="

cd deployment/docker
docker-compose down

echo "✓ All services stopped"
