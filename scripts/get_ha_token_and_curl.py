
import yaml
import subprocess
import os

# Define the path to your secrets.yaml file
SECRETS_FILE_PATH = "Docker/config/secrets.yaml"
# Define the entity ID and Home Assistant instance
ENTITY_ID = "sensor.price_buywisely_type_motorola_moto_g75_5g_256gb_grey_with_buds"
HA_INSTANCE = "localhost:8123"

def get_api_token(secrets_file):
    try:
        with open(secrets_file, 'r') as f:
            secrets = yaml.safe_load(f)
        # Assuming the token is directly under 'homeassistant_api_token'
        token = secrets.get('homeassistant_api_token')
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
        "-X", "GET",
        "-H", f"Authorization: Bearer {token}",
        "-H", "Content-Type: application/json",
        f"http://{ha_instance}/api/states/{entity_id}"
    ]
    try:
        result = subprocess.run(curl_command, capture_output=True, text=True, check=True)
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
    api_token = get_api_token(SECRETS_FILE_PATH)
    if api_token:
        run_curl_command(api_token, HA_INSTANCE, ENTITY_ID)
