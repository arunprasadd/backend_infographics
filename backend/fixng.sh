#!/bin/bash

echo "🔧 Complete nginx configuration fix..."

# Stop all containers completely
echo "1. Stopping all containers..."
docker-compose -f docker-compose.prod.yml down --remove-orphans

# Remove nginx container and any cached volumes
echo "2. Removing nginx container completely..."
docker rm -f infographic_nginx 2>/dev/null || true

# Check what file is actually being mounted
echo "3. Checking docker-compose nginx volume configuration..."
grep -A 10 "nginx:" docker-compose.prod.yml | grep -A 5 "volumes:"

# Find and remove ALL nginx config files to start fresh
echo "4. Removing all existing nginx config files..."
rm -f nginx/*.conf

# Create the nginx directory if it doesn't exist
mkdir -p nginx

# Create a completely clean nginx.conf
echo "5. Creating clean nginx.conf..."
cat > nginx/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/conf.d/*.conf;
}
EOF

# Create the correct default.conf (this is what gets mounted as default.conf)
echo "6. Creating correct default.conf..."
cat > nginx/default.conf << 'EOF'
server {
    listen 80;
    server_name api.videotoinfographics.com;

    # CORS Headers
    add_header Access-Control-Allow-Origin "*" always;
    add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
    add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;

    location / {
        if ($request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin "*" always;
            add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
            add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;
            add_header Access-Control-Max-Age 1728000;
            add_header Content-Type 'text/plain charset=UTF-8';
            add_header Content-Length 0;
            return 204;
        }

        # Proxy to API container (using correct container name)
        proxy_pass http://infographic_api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

# Also create api-simple.conf in case that's what's being mounted
echo "7. Creating api-simple.conf as backup..."
cp nginx/default.conf nginx/api-simple.conf

# Update docker-compose to use the correct file
echo "8. Updating docker-compose to use default.conf..."
sed -i 's|./nginx/api-simple.conf:/etc/nginx/conf.d/default.conf|./nginx/default.conf:/etc/nginx/conf.d/default.conf|g' docker-compose.prod.yml

# Start only the API and database services first
echo "9. Starting API and database services first..."
docker-compose -f docker-compose.prod.yml up -d postgres redis infographic_api

# Wait for API to be ready
echo "10. Waiting for API to be ready..."
sleep 15

# Test direct API access
echo "11. Testing direct API access..."
if curl -s http://localhost:8000/api/health > /dev/null; then
    echo "✅ API is responding directly"
else
    echo "❌ API not responding - check API container"
    docker logs infographic_api --tail 10
    exit 1
fi

# Now start nginx with the clean configuration
echo "12. Starting nginx with clean configuration..."
docker-compose -f docker-compose.prod.yml up -d nginx

# Wait and check nginx status
echo "13. Waiting for nginx to start..."
sleep 10

echo "14. Checking nginx status..."
if docker ps | grep nginx | grep -q "Up"; then
    echo "✅ Nginx is running"
else
    echo "❌ Nginx failed to start"
    docker logs infographic_nginx --tail 20
    exit 1
fi

echo "15. Testing external connection..."
if curl -s http://api.videotoinfographics.com/api/health > /dev/null; then
    echo "✅ External connection working!"
    echo "🎉 nginx fix complete and working!"
else
    echo "❌ External connection failed"
    echo "Checking nginx logs..."
    docker logs infographic_nginx --tail 10
fi

echo "16. Final status check..."
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
