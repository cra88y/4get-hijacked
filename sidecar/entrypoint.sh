#!/bin/bash
set -e

REPO_DIR="/var/www/html/4get-repo"
CONFIG_FILE="$REPO_DIR/data/config.php"

# 1. Ensure Repo Exists
if [ ! -d "$REPO_DIR" ]; then
    echo "📥 4get-repo not found, cloning..."
    git clone --depth 1 https://git.lolcat.ca/lolcat/4get.git "$REPO_DIR"
fi

# 2. Configure 4get User-Agent to match curl-impersonate-chrome v116
# This ensures the TLS fingerprint matches the HTTP Header
CHROME_UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"

echo "⚙️  Configuring 4get User-Agent..."

if [ -f "$CONFIG_FILE" ]; then
    # Replace the User Agent line in the config file on disk
    sed -i "s|const USER_AGENT = \".*\";|const USER_AGENT = \"$CHROME_UA\";|g" "$CONFIG_FILE"
    echo "✅ User-Agent set to Chrome 116."
else
    echo "⚠️  Config file not found at $CONFIG_FILE. Skipping UA patch."
fi

exec "$@"