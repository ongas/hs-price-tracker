#!/bin/bash
# Deployment script for price_tracker custom component
# IMPORTANT: Only deploy the inner source directory, never the project root!
# Project root:      custom_components/price_tracker
# Deployment source: custom_components/price_tracker/custom_components/price_tracker
# Deployment target: ../../docker/config/custom_components/price_tracker

set -e

SRC="../custom_components/price_tracker/custom_components/price_tracker/"
DST="../../docker/config/custom_components/price_tracker/"
DOCKER_DIR="../../docker"
HA_LOG="$DOCKER_DIR/config/home-assistant.log"

step() {
  echo -e "\n========== $1 =========="
}

summary=""

step "1. Stopping Home Assistant container"
cd "$DOCKER_DIR"
docker compose stop homeassistant && summary+="Stopped Home Assistant container.\n"

step "2. Deleting Home Assistant log file"
if [ -f "$HA_LOG" ]; then
  rm "$HA_LOG" && summary+="Deleted HA log file.\n"
else
  summary+="HA log file not found, skipping.\n"
fi

step "3. Deleting all __pycache__ files in deployment target"
find "$DST" -type d -name '__pycache__' -exec rm -rf {} + && summary+="Deleted __pycache__ files in deployment target.\n"

step "4. Deploying code via rsync"
rsync -av --exclude='__pycache__' --exclude='*.pyc' --delete "$SRC" "$DST" && summary+="Deployed code to HA config.\n"

step "5. Starting Home Assistant container"
docker compose start homeassistant && summary+="Started Home Assistant container.\n"

step "6. Deployment Summary"
echo -e "\n========== DEPLOYMENT SUMMARY =========="
echo -e "$summary"
echo "Deployment complete. Home Assistant is restarting with the latest code."
