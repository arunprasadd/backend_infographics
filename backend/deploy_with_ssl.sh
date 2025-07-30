#!/bin/bash

DOMAIN=${1:-api.videotoinfographics.com}
EMAIL=${2:-admin@videotoinfographics.com}

echo "🚀 Deploying Backend with SSL for domain: $DOMAIN"

# Update domain in nginx config
sed -i "s/api.videotoinfographics.com/$DOMAIN/g" nginx/api.conf

# Update email in docker-compose
sed -i "s/your-email@example.com/$EMAIL/g" docker-compose.prod.yml

# Create directories
mkdir -p certbot/conf certbot/www

echo "📦 Starting API and database services first (NO nginx yet)..."
# Start only API, postgres, redis - NOT nginx
docker-compose -f docker-compose.prod.yml up -d api postgres redis

# Wait for API to be ready
echo "⏳ Waiting for API to be ready..."
sleep 10

# Test if API is accessible directly
echo "🔍 Testing API accessibility..."
curl -f http://localhost:8000/api/health || echo "⚠️  API not ready yet"

echo "🔒 Getting SSL certificate using standalone mode (port 80 free)..."
# Use certbot standalone mode since nginx isn't running yet
docker run --rm \
    -p 80:80 \
    -v $(pwd)/certbot/conf:/etc/letsencrypt \
    -v $(pwd)/certbot/www:/var/www/certbot \
    certbot/certbot certonly \
    --standalone \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN

# Check if certificate was created
if [ -f "certbot/conf/live/$DOMAIN/fullchain.pem" ]; then
    echo "✅ SSL certificate obtained successfully!"
    
    echo "🚀 Now starting nginx with SSL configuration..."
    # Now start nginx with SSL certificates available
    docker-compose -f docker-compose.prod.yml up -d nginx
    
    SSL_AVAILABLE=true
else
    echo "❌ SSL certificate generation failed!"
    echo "🔄 Starting nginx with HTTP-only configuration..."
    
    # Create HTTP-only nginx config
    cat > nginx/api-http.conf << EOF
server {
    listen 80;
    server_name $DOMAIN;

    # CORS Headers
    add_header Access-Control-Allow-Origin "*" always;
    add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
    add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;

    location / {
        if (\$request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin "*" always;
            add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
            add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;
            add_header Access-Control-Max-Age 1728000;
            add_header Content-Type 'text/plain charset=UTF-8';
            add_header Content-Length 0;
            return 204;
        }

        proxy_pass http://api:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
    
    # Update docker-compose to use HTTP-only config
    sed -i 's|./nginx/api.conf:/etc/nginx/conf.d/default.conf|./nginx/api-http.conf:/etc/nginx/conf.d/default.conf|g' docker-compose.prod.yml
    
    # Start nginx with HTTP config
    docker-compose -f docker-compose.prod.yml up -d nginx
    
    SSL_AVAILABLE=false
fi

# Ensure all services are running
echo "🚀 Ensuring all services are running..."
docker-compose -f docker-compose.prod.yml up -d --remove-orphans

# Setup SSL renewal cron job (only if SSL is available)
if [ "$SSL_AVAILABLE" = true ]; then
    echo "⏰ Setting up SSL renewal..."
    (crontab -l 2>/dev/null; echo "0 12 * * * cd $(pwd) && docker-compose -f docker-compose.prod.yml run --rm certbot renew --quiet && docker-compose -f docker-compose.prod.yml restart nginx") | crontab -
fi

echo "✅ Deployment complete!"

# Show appropriate URLs
if [ "$SSL_AVAILABLE" = true ]; then
    echo "🌐 API available at: https://$DOMAIN"
    echo "📚 API docs at: https://$DOMAIN/docs"
    echo "❤️ Health check: https://$DOMAIN/api/health"
else
    echo "🌐 API available at: http://$DOMAIN"
    echo "📚 API docs at: http://$DOMAIN/docs"
    echo "❤️ Health check: http://$DOMAIN/api/health"
    echo "⚠️  SSL certificate not available - using HTTP only"
fi

# Show container status
echo ""
echo "📊 Container Status:"
docker-compose -f docker-compose.prod.yml ps
