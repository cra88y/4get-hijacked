#!/bin/bash
set -e

REPO_DIR="/var/www/html/4get-repo"
CONFIG_FILE="$REPO_DIR/data/config.php"

# 1. Ensure Repo Exists (Fallback)
if [ ! -d "$REPO_DIR" ]; then
    echo "📥 4get-repo not found, cloning..."
    git clone --depth 1 https://git.lolcat.ca/lolcat/4get.git "$REPO_DIR"
fi

# 2. AUTOMATION: Configure 4get
# We define the UA that matches curl-impersonate-chrome v116
CHROME_UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"

echo "⚙️  Configuring 4get User-Agent..."

# If config.php doesn't exist, look for a default or create one
if [ ! -f "$CONFIG_FILE" ]; then
    # 4get usually has config.php in the repo, but if not, we might need to copy a default
    # For now, we assume the repo provides a valid config.php or we edit it in place.
    echo "   Checking for config file..."
fi

# Use sed to replace the User Agent line in the config file
# This modifies the actual file on disk, so PHP reads it natively.
sed -i "s|const USER_AGENT = \".*\";|const USER_AGENT = \"$CHROME_UA\";|g" "$CONFIG_FILE"

echo "✅ User-Agent set to Chrome 116."

# 3. Fix Permissions
chown -R www-data:www-data /var/www/html

exec "$@"