#!/bin/bash
set -e
REPO_DIR="/var/www/html/4get-repo"
git config --global --add safe.directory /var/www/html/4get-repo
# Auto-update logic
if [ ! -d "$REPO_DIR" ]; then
    echo "📥 Cloning 4get..."
    git clone https://git.lolcat.ca/lolcat/4get.git "$REPO_DIR"
else
    echo "🔄 Updating 4get..."
    cd "$REPO_DIR"
    git pull origin master || echo "⚠️ Git pull failed, continuing..."
    cd ..
fi

chown -R www-data:www-data /var/www/html || echo "⚠️ chown failed, continuing..."
exec "$@"