#!/bin/bash
# Database backup script
# Run this on the server via cron: 0 3 * * * /home/shoeapp/backup_db.sh

BACKUP_DIR="/home/shoeapp/backups"
DB_PATH="/home/shoeapp/shoe_store_perm/instance/shop.db"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Create backup
if [ -f "$DB_PATH" ]; then
    cp "$DB_PATH" "$BACKUP_DIR/shop_$DATE.db"
    echo "✅ Backup created: shop_$DATE.db"
    
    # Compress old backups (optional)
    gzip "$BACKUP_DIR/shop_$DATE.db" 2>/dev/null || true
    
    # Delete backups older than 30 days
    find "$BACKUP_DIR" -name "shop_*.db*" -mtime +30 -delete
    echo "🧹 Cleaned up backups older than 30 days"
else
    echo "❌ Database file not found: $DB_PATH"
    exit 1
fi

