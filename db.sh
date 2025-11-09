#!/bin/bash

# BacklineMD Database Setup Script
# This script starts MongoDB in Docker and seeds the database

set -e  # Exit on error

echo "🚀 Starting BacklineMD Database Setup..."
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Start MongoDB in Docker
echo -e "${YELLOW}Step 1: Starting MongoDB in Docker...${NC}"

# Check if MongoDB container already exists
if docker ps -a --format '{{.Names}}' | grep -q "^mongodb$"; then
    echo "   MongoDB container already exists"
    
    # Check if it's running
    if docker ps --format '{{.Names}}' | grep -q "^mongodb$"; then
        echo -e "   ${GREEN}✓ MongoDB is already running${NC}"
    else
        echo "   Starting existing MongoDB container..."
        docker start mongodb
        echo -e "   ${GREEN}✓ MongoDB container started${NC}"
    fi
else
    echo "   Creating new MongoDB container..."
    docker run -d \
        --name mongodb \
        -p 27017:27017 \
        -v mongodb_data:/data/db \
        mongo:latest
    echo -e "   ${GREEN}✓ MongoDB container created and started${NC}"
fi

# Wait for MongoDB to be ready
echo ""
echo -e "${YELLOW}Waiting for MongoDB to be ready...${NC}"
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if docker exec mongodb mongosh --eval "db.adminCommand('ping')" --quiet > /dev/null 2>&1; then
        echo -e "   ${GREEN}✓ MongoDB is ready!${NC}"
        break
    fi
    
    attempt=$((attempt + 1))
    echo "   Attempt $attempt/$max_attempts..."
    sleep 1
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "   ${RED}✗ MongoDB failed to start after $max_attempts attempts${NC}"
    exit 1
fi

# Step 2: Seed the database
echo ""
echo -e "${YELLOW}Step 2: Seeding database with initial data...${NC}"

# Check if we're in the right directory
if [ ! -f "backend/seed_data.py" ]; then
    echo -e "   ${RED}✗ Error: backend/seed_data.py not found${NC}"
    echo "   Please run this script from the project root directory"
    exit 1
fi

# Run seed data script
cd backend
python seed_data.py
SEED_EXIT_CODE=$?
cd ..

if [ $SEED_EXIT_CODE -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Database seeded successfully!${NC}"
    echo ""
    echo "MongoDB is running on: mongodb://localhost:27017"
    echo "Database name: backlinemd"
    echo ""
    echo "To stop MongoDB: docker stop mongodb"
    echo "To start MongoDB: docker start mongodb"
    echo "To remove MongoDB: docker rm -f mongodb"
else
    echo ""
    echo -e "${RED}✗ Failed to seed database${NC}"
    exit 1
fi

