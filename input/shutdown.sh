#!/bin/bash

# Shutdown script for the test CRUD service
# This script uses docker-compose to stop the service

set -e

echo "🛑 Shutting down Test CRUD Service with docker-compose..."

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ docker-compose is not available. Please install docker-compose."
    exit 1
fi

# Use docker-compose to stop the service
echo "⏹️  Stopping services..."
if command -v docker-compose &> /dev/null; then
    docker-compose down
else
    docker compose down
fi

if [ $? -eq 0 ]; then
    echo "✅ Service stopped successfully"
    echo ""
    echo "🧹 All containers and networks have been cleaned up"
else
    echo "⚠️  Service may have already been stopped or encountered an error"
fi
