# Deployment Notes for price_tracker Custom Component

- Only the contents of `custom_components/price_tracker/` are deployed to Home Assistant.
- The deployment script (`DEPLOYMENT_SCRIPT.sh`) copies only the required files and directories to the dev container location: `/mnt/e/Source/Repos/homeassistant/Docker/config/custom_components/price_tracker/`.
- Tests, backups, and development files are excluded from deployment.
- Update your Docker `ha-dev` container volume mount to reference `/mnt/e/Source/Repos/homeassistant/Docker/config/custom_components/price_tracker/` for the custom component.
- After deployment, restart Home Assistant in the dev container to load the updated component.
