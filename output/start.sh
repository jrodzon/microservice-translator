#!/bin/bash

# Startup script for the test CRUD service
# This script uses docker-compose to start the service

set -e

echo "🚀 Starting Test CRUD Service with docker-compose..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ docker-compose is not available. Please install docker-compose."
    exit 1
fi

# Use docker-compose to start the service
echo "🔨 Building and starting services..."
if command -v docker-compose &> /dev/null; then
    docker-compose up -d --build
else
    docker compose up -d --build
fi

if [ $? -eq 0 ]; then
    echo "✅ Service started successfully"
    echo ""
    echo "🌐 Service is running at: http://localhost:8000"
    echo "📋 API Documentation: http://localhost:8000/docs"
    echo "❤️  Health Check: http://localhost:8000/health"
    echo ""
    echo "📊 Container status:"
    if command -v docker-compose &> /dev/null; then
        docker-compose ps
    else
        docker compose ps
    fi
    echo ""
    echo "📝 To view logs: docker-compose logs -f (or docker compose logs -f)"
    echo "🛑 To stop: ./shutdown.sh"
else
    echo "❌ Failed to start service"
    exit 1
fi
