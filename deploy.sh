#!/bin/bash
# Deployment script for shoe_store_perm
# Run this on the server: bash /home/shoeapp/Perm_shop/deploy.sh

set -e  # Exit on error

echo "🚀 Starting deployment..."

cd /home/shoeapp/Perm_shop

# Activate virtual environment
source .venv/bin/activate

# Pull latest code
echo "📥 Pulling latest code..."
git pull origin main

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Restart service
echo "🔄 Restarting service..."
sudo systemctl restart shoeapp

# Wait a moment for service to start
sleep 2

# Check service status
if sudo systemctl is-active --quiet shoeapp; then
    echo "✅ Deployment completed successfully!"
    echo "📊 Service status:"
    sudo systemctl status shoeapp --no-pager -l
else
    echo "❌ Deployment failed! Service is not running."
    sudo systemctl status shoeapp --no-pager -l
    exit 1
fi

