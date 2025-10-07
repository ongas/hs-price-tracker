import yaml
import subprocess
import os

# Define the path to the configuration file
CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), "call_ha_api_config.yaml")


def load_config(config_file):
    try:
        with open(config_file, "r") as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"Error: Configuration file not found at {config_file}")
        exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing configuration file: {e}")
        exit(1)


def get_api_token(secrets_file):
    try:
        with open(secrets_file, "r") as f:
            secrets = yaml.safe_load(f)
        token = secrets.get("homeassistant_api_token")
        if not token:
            print(f"Error: 'homeassistant_api_token' not found in {secrets_file}")
            return None
        return token
    except FileNotFoundError:
        print(f"Error: secrets.yaml not found at {secrets_file}")
        return None
    except yaml.YAMLError as e:
        print(f"Error parsing secrets.yaml: {e}")
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
        result = subprocess.run(
            curl_command, capture_output=True, text=True, check=True
        )
        print("Curl Command Output:")
        print(result.stdout)
        if result.stderr:
            print("Curl Command Error (stderr):")
            print(result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Error executing curl command: {e}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


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
