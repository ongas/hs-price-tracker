#!/bin/bash
# Deployment script for Home Assistant price_tracker custom component
# Usage: Run from the root of the repo: ./DEPLOYMENT_SCRIPT.sh

# Load deployment config
CONFIG_FILE="$(cd "$(dirname "$0")" && pwd)/DEPLOYMENT_CONFIG.sh"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "ERROR: Deployment config file $CONFIG_FILE not found. Please create it with the required parameters."
    exit 1
fi
source "$CONFIG_FILE"

SRC_DIR="$(cd "$(dirname "$0")" && pwd)/custom_components/price_tracker"

echo "[DEPLOY] Removing old deployed version at $TARGET_DIR..."
rm -rf "$TARGET_DIR"

echo "[DEPLOY] Creating target directory $TARGET_DIR..."
mkdir -p "$TARGET_DIR"

echo "[DEPLOY] Copying files from $SRC_DIR to $TARGET_DIR..."
cp -vr $SRC_DIR/* "$TARGET_DIR/"

echo "[DEPLOY] Removing scripts, test, and Docker directories from $TARGET_DIR..."
rm -rf "$TARGET_DIR/scripts" "$TARGET_DIR/test" "$TARGET_DIR/tests" "$TARGET_DIR/Docker"

echo "[DEPLOY] Removing Docker directories from source if present..."
find "$SRC_DIR" -type d -name Docker -prune -exec rm -rf {} +

echo "[DEPLOY] Deployment complete."