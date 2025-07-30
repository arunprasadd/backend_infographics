#!/bin/bash

echo "🔒 Setting up SSL for api.videotoinfographics.com..."

DOMAIN="api.videotoinfographics.com"
EMAIL="admin@videotoinfographics.com"

# Stop nginx temporarily to free port 80 for certbot
echo "1. Stopping nginx temporarily..."
docker-compose -f docker-compose.prod.yml stop nginx

# Create directories for certbot
echo "2. Creating certbot directories..."
mkdir -p certbot/conf certbot/www

# Get SSL certificate using standalone mode (port 80 free)
echo "3. Getting SSL certificate..."
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
    
    # Create SSL-enabled nginx configuration
    echo "4. Creating SSL-enabled nginx configuration..."
    cat > nginx/default.conf << 'EOF'
# HTTP server - redirect to HTTPS
server {
    listen 80;
    server_name api.videotoinfographics.com;

    # Let's Encrypt challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
        try_files $uri $uri/ =404;
        allow all;
    }

    # Redirect all other HTTP traffic to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name api.videotoinfographics.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/api.videotoinfographics.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.videotoinfographics.com/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;

    # CORS Headers
    add_header Access-Control-Allow-Origin "*" always;
    add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
    add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;

    # Handle preflight requests
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

        # Proxy to API container
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

    echo "5. Starting nginx with SSL configuration..."
    docker-compose -f docker-compose.prod.yml start nginx
    
    # Setup SSL renewal cron job
    echo "6. Setting up SSL renewal..."
    (crontab -l 2>/dev/null; echo "0 12 * * * cd $(pwd) && docker-compose -f docker-compose.prod.yml run --rm certbot renew --quiet && docker-compose -f docker-compose.prod.yml restart nginx") | crontab -
    
    echo "✅ SSL setup complete!"
    echo "🌐 API now available at: https://$DOMAIN"
    echo "📚 API docs at: https://$DOMAIN/docs"
    echo "❤️ Health check: https://$DOMAIN/api/health"
    
else
    echo "❌ SSL certificate generation failed!"
    echo "🔄 Starting nginx with HTTP-only configuration..."
    
    # Revert to HTTP-only configuration
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

        # Proxy to API container
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
    
    docker-compose -f docker-compose.prod.yml start nginx
    
    echo "🌐 API available at: http://$DOMAIN (HTTP only)"
    echo "⚠️  SSL certificate not available - using HTTP only"
fi

echo ""
echo "📊 Final Container Status:"
docker-compose -f docker-compose.prod.yml ps
