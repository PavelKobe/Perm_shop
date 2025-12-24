#!/bin/bash
# Script to deploy images to server
# Run this from your local machine (Windows: use Git Bash or WSL)

set -e

# Configuration - CHANGE THESE!
SERVER_USER="shoeapp"
SERVER_HOST="your-server-ip-or-domain"
SERVER_PATH="/home/shoeapp/shoe_store_perm/static/images/products"

# Local path to images
LOCAL_PATH="./static/images/products"

echo "📤 Deploying images to server..."

# Check if rsync is available
if ! command -v rsync &> /dev/null; then
    echo "❌ rsync not found. Please install it or use SFTP client (WinSCP, FileZilla)"
    exit 1
fi

# Deploy images
rsync -avz --progress --delete \
    "$LOCAL_PATH/" \
    "$SERVER_USER@$SERVER_HOST:$SERVER_PATH/"

echo "✅ Images deployed successfully!"

# Set correct permissions on server
echo "🔐 Setting permissions..."
ssh "$SERVER_USER@$SERVER_HOST" "chown -R shoeapp:shoeapp $SERVER_PATH && chmod -R 755 $SERVER_PATH"

echo "🎉 All done!"

