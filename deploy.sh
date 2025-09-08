#!/bin/bash
# Deploy price_tracker custom component to Home Assistant dev container

SRC_DIR="/mnt/e/Source/Repos/homeassistant/custom/price_tracker/custom_components/price_tracker"
TARGET_DIR="/mnt/e/Source/Repos/homeassistant/Docker/config/custom_components/price_tracker"

# Create target directory if it doesn't exist
mkdir -p "$TARGET_DIR"

# Rsync only relevant files and folders
rsync -av --exclude='tests' --exclude='backup*' --exclude='*.md' --exclude='*.pyc' --exclude='__pycache__' --exclude='.ruff_cache' --exclude='.pytest_cache' --exclude='.git' --exclude='.github' --exclude='.DS_Store' --exclude='.docs' --exclude='images' "$SRC_DIR/" "$TARGET_DIR/"

echo "Deployment complete. Custom component is now available at $TARGET_DIR for Home Assistant dev container."
