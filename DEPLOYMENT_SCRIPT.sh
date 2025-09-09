#!/bin/bash
# Deployment script for Home Assistant price_tracker custom component
# Usage: Run from the root of the repo: ./DEPLOYMENT_SCRIPT.sh

SRC_DIR="$(cd "$(dirname "$0")" && pwd)/custom_components/price_tracker"
TARGET_DIR="/mnt/e/Source/Repos/homeassistant/Docker/config/custom_components/price_tracker"

# Remove old deployed version
rm -rf "$TARGET_DIR"


# Copy only essential files and directories, excluding scripts/
mkdir -p "$TARGET_DIR"
# Copy everything, then remove unwanted directories/files
cp -r $SRC_DIR/* "$TARGET_DIR/"
# Remove scripts, Docker, and other non-essential files from the target
rm -rf "$TARGET_DIR/scripts" "$TARGET_DIR/test" "$TARGET_DIR/tests" "$TARGET_DIR/Docker"

# Remove Docker directory from source before copying (prevents recursion)
find "$SRC_DIR" -type d -name Docker -prune -exec rm -rf {} +

echo "Deployment complete."
