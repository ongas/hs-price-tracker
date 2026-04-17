import yaml
import subprocess
import os

# Define the path to the configuration file
CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), "call_ha_api_config.yaml")


def load_config(config_file_path):
    with open(config_file_path, "r") as f:
        return yaml.safe_load(f)


def get_api_token(secrets_file_path):
    try:
        with open(secrets_file_path, "r") as f:
            secrets = yaml.safe_load(f)
            return secrets.get("ha_api_token")
    except FileNotFoundError:
        print(f"Error: Secrets file not found at {secrets_file_path}")
        return None


def run_curl_command(token, ha_instance, entity_id):
    curl_command = [
        "curl",
        "-X",
        "GET",
        "-H",
        f"Authorization: Bearer {token}",
        "-H",
        "Content-Type: application/json",
        f"http://{ha_instance}/api/states/{entity_id}",
    ]

    try:
        result = subprocess.run(curl_command, capture_output=True, text=True, check=True)
        print("Curl Command Output:")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error executing curl command: {e}")
        print(f"Stderr: {e.stderr}")
    except FileNotFoundError:
        print("Error: 'curl' command not found. Please ensure curl is installed and in your PATH.")


if __name__ == "__main__":
    config = load_config(CONFIG_FILE_PATH)

    secrets_file_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), config.get("secrets_file_path"))
    )
    ha_instance = config.get("ha_instance")

    # Support both 'entity_id' (single) and 'entity_ids' (list)
    entity_ids = config.get("entity_ids")
    if not entity_ids:
        entity_id = config.get("entity_id")
        if entity_id:
            entity_ids = [entity_id]
        else:
            entity_ids = []

    if not all([secrets_file_path, entity_ids, ha_instance]) or not entity_ids:
        print("Error: Missing configuration values in config.yaml")
        exit(1)

    api_token = get_api_token(secrets_file_path)
    if api_token:
        for eid in entity_ids:
            print(f"\n--- Retrieving entity: {eid} ---")
            run_curl_command(api_token, ha_instance, eid)