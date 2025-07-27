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

# Start nginx first (without SSL)
echo "📦 Starting Nginx for Let's Encrypt challenge..."
docker-compose -f docker-compose.prod.yml up -d nginx

# Wait for nginx to be ready
sleep 10

# Get SSL certificate
echo "🔒 Obtaining SSL certificate..."
docker-compose -f docker-compose.prod.yml run --rm certbot certonly \
    --webroot \
    --webroot-path /var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN

# Restart nginx with SSL
echo "🔄 Restarting Nginx with SSL..."
docker-compose -f docker-compose.prod.yml restart nginx

# Start all services
echo "🚀 Starting all services..."
docker-compose -f docker-compose.prod.yml up -d

# Setup SSL renewal cron job
echo "⏰ Setting up SSL renewal..."
(crontab -l 2>/dev/null; echo "0 12 * * * cd $(pwd) && docker-compose -f docker-compose.prod.yml run --rm certbot renew --quiet && docker-compose -f docker-compose.prod.yml restart nginx") | crontab -

echo "✅ Deployment complete!"
echo "🌐 API available at: https://$DOMAIN"
echo "📚 API docs at: https://$DOMAIN/docs"
echo "❤️ Health check: https://$DOMAIN/api/health"
