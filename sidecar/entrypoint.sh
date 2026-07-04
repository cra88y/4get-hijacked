#!/bin/bash
set -e

REPO_DIR="/var/www/html/4get-repo"
CONFIG_FILE="$REPO_DIR/data/config.php"

if [ ! -d "$REPO_DIR" ]; then
    echo "📥 4get-repo not found, cloning..."
    git clone --depth 1 https://git.lolcat.ca/lolcat/4get.git "$REPO_DIR"
fi

FIREFOX_UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:117.0) Gecko/20100101 Firefox/117.0"
echo "⚙️  Configuring 4get..."

if [ -f "$CONFIG_FILE" ]; then
    sed -i -E "s|const\s+USER_AGENT\s*=\s*\".*\";|const USER_AGENT = \"$FIREFOX_UA\";|g" "$CONFIG_FILE"
    echo "✅ User-Agent set to Firefox 117."
else
    echo "⚠️  Config not found. Skipping UA patch."
fi

DDG_SCRAPER="$REPO_DIR/scraper/ddg.php"
if [ -f "$DDG_SCRAPER" ]; then
    sed -i -E 's/return\s+\$this->web_full\(\$get\)\s*;/return $this->web_html($get);/' "$DDG_SCRAPER"
    echo "✅ DDG patched to HTML endpoint."
fi

echo "📦 Generating manifest..."
php /var/www/html/generate_manifest.php

if ! grep -q "HostnameLookups Off" /etc/apache2/apache2.conf; then
    echo "HostnameLookups Off" >> /etc/apache2/apache2.conf
    echo "ServerName localhost" >> /etc/apache2/apache2.conf
    echo "✅ Apache DNS lookups disabled and ServerName set."
fi

exec "$@"