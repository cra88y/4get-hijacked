#!/bin/bash
set -e

REPO_DIR="/var/www/html/4get-repo"
CONFIG_FILE="$REPO_DIR/data/config.php"

# 1. Ensure Repo Exists
if [ ! -d "$REPO_DIR" ]; then
    echo "📥 4get-repo not found, cloning..."
    git clone --depth 1 https://git.lolcat.ca/lolcat/4get.git "$REPO_DIR"
fi

# 2. Configure 4get User-Agent to match curl-impersonate-ff v117
# This ensures the TLS fingerprint matches the HTTP Header
FIREFOX_UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:117.0) Gecko/20100101 Firefox/117.0"

echo "⚙️  Configuring 4get User-Agent..."

if [ -f "$CONFIG_FILE" ]; then
    # Replace the User Agent line in the config file on disk
    sed -i "s|const USER_AGENT = \".*\";|const USER_AGENT = \"$FIREFOX_UA\";|g" "$CONFIG_FILE"
    echo "✅ User-Agent set to Firefox 117."
else
    echo "⚠️  Config file not found at $CONFIG_FILE. Skipping UA patch."
fi

# 3. Synchronize Manifest
echo "📦 Synchronizing manifest with scrapers..."
php /var/www/html/generate_manifest.php

exec "$@"