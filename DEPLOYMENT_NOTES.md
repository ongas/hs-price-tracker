# Deployment Notes for price_tracker Custom Component

- **Deployment Method:** Use the provided deployment script (`DEPLOYMENT_SCRIPT.sh`) located at `custom_components/price_tracker/DEPLOYMENT_SCRIPT.sh` to deploy the custom component. This script copies only the required files and directories to the dev container location: `/mnt/e/Source/Repos/homeassistant/Docker/config/custom_components/price_tracker/`.
- Tests, backups, and development files are excluded from deployment.
- Update your Docker `ha-dev` container volume mount to reference `/mnt/e/Source/Repos/homeassistant/Docker/config/custom_components/price_tracker/` for the custom component.
- After deployment, restart Home Assistant in the dev container to load the updated component.

## Dependency Management for Docker Environment

If the custom component requires additional Python packages not included in the Home Assistant Docker image, you will need to install them manually inside the running container.

1.  **Start the Home Assistant Container (if not already running):**
    ```bash
    cd /mnt/e/Source/Repos/homeassistant/Docker && docker compose start homeassistant
    ```

2.  **Install Python Packages:**
    Execute `pip install` commands inside the `homeassistant` service container. For example, to install `nextjs-hydration-parser`:
    ```bash
    cd /mnt/e/Source/Repos/homeassistant/Docker && docker compose exec homeassistant pip install nextjs-hydration-parser
    ```
    Replace `nextjs-hydration-parser` with the name of the required package.

## Post-Deployment Steps

1.  **Restart Home Assistant Docker Container:**
    Navigate to the `Docker` directory and restart the container.
    ```bash
    cd /mnt/e/Source/Repos/homeassistant/Docker && docker compose restart homeassistant
    ```

2.  **Check Home Assistant Logs:**
    Monitor the Home Assistant logs for any errors or relevant information regarding the `price_tracker` component. The log file is typically located at:
    `/mnt/e/Source/Repos/homeassistant/Docker/config/home-assistant.log`
    You can monitor it using:
    ```bash
    tail -f /mnt/e/Source/Repos/homeassistant/Docker/config/home-assistant.log
    ```
    **Note for Agent:** The agent cannot directly access files outside the project directory or within Docker containers. If the agent requests log content, you may need to manually retrieve and provide it.
