#!/bin/bash

echo "🚀 Starting services with correct configuration..."

# Start all services
echo "1. Starting all services..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be ready
echo "2. Waiting for services to start..."
sleep 15

# Check container status
echo "3. Checking container status..."
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Test API directly
echo "4. Testing API directly..."
if curl -s http://localhost:8000/api/health > /dev/null; then
    echo "✅ API is responding directly"
else
    echo "❌ API not responding directly"
    echo "API logs:"
    docker logs infographic_api --tail 10
fi

# Test through nginx
echo "5. Testing through nginx..."
if curl -s http://api.videotoinfographics.com/api/health > /dev/null; then
    echo "✅ External connection working!"
    echo "🎉 All services are working correctly!"
else
    echo "❌ External connection failed"
    echo "Nginx logs:"
    docker logs infographic_nginx --tail 10
fi

echo "6. Final status:"
docker ps | grep -E "(nginx|api|postgres|redis)"
