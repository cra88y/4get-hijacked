#!/bin/bash
set -e
REPO_DIR="/var/www/html/4get-repo"

# Auto-update logic
if [ ! -d "$REPO_DIR" ]; then
    echo "📥 Cloning 4get..."
    git clone https://git.4get.ca/4get/4get "$REPO_DIR"
else
    echo "🔄 Updating 4get..."
    cd "$REPO_DIR"
    git pull origin master || echo "⚠️ Git pull failed, continuing..."
    cd ..
fi

chown -R www-data:www-data /var/www/html || echo "⚠️ chown failed, continuing..."
exec "$@"