#!/bin/bash
# Deployment script for Home Assistant price_tracker custom component
# Usage: Run from the root of the repo: ./DEPLOYMENT_SCRIPT.sh

SRC_DIR="$(pwd)/custom_components/price_tracker"
TARGET_DIR="/mnt/e/Source/Repos/homeassistant/Docker/config/custom_components/price_tracker"

# Remove old deployed version
rm -rf "$TARGET_DIR"

# Copy new version
mkdir -p "$TARGET_DIR"
cp -r $SRC_DIR/* "$TARGET_DIR/"

echo "Deployment complete."
