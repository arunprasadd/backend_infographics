#!/bin/bash

# YouTube to Infographic API Deployment Script
# Usage: ./deploy.sh

set -e

echo "🚀 Starting deployment..."

# Build Docker image
echo "📦 Building Docker image..."
docker build -t youtube-infographic-api .

# Stop existing container if running
echo "🛑 Stopping existing container..."
docker stop youtube-infographic-api || true
docker rm youtube-infographic-api || true

# Run new container
echo "▶️ Starting new container..."
docker run -d \
  --name youtube-infographic-api \
  --restart unless-stopped \
  -p 8000:8000 \
  -e PORT=8000 \
  -e HOST=0.0.0.0 \
  -e DEBUG=false \
  -e LOG_LEVEL=info \
  youtube-infographic-api

echo "✅ Deployment complete!"
echo "🌐 API available at: http://your-vm-ip:8000"
echo "📚 API docs at: http://your-vm-ip:8000/docs"
echo "❤️ Health check: http://your-vm-ip:8000/api/health"

# Show container status
docker ps | grep youtube-infographic-api