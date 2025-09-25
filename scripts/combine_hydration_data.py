
import json

def combine_hydration_data():
    """
    Combines and cleans the fragmented hydration data into a single JSON file.
    """
    try:
        with open("/mnt/e/source/personal_repos/homeassistant/custom_components/price_tracker/hydration_data.json", "r", encoding="utf-8") as f:
            hydration_fragments = json.load(f)

        # This is a simplified approach. A more robust solution would involve
        # more sophisticated parsing of the JavaScript-like syntax.
        full_data_str = "".join(hydration_fragments)

        # Basic cleaning of the combined string to make it more JSON-like
        # This is still a hack and might not work for all cases.
        # Remove [1, and ] at the beginning and end
        full_data_str = full_data_str.replace("[1,", "[").replace("]", "")
        # Remove escaped quotes
        full_data_str = full_data_str.replace('\"', '"')

        # Attempt to save it as a single string for now
        with open("/mnt/e/source/personal_repos/homeassistant/custom_components/price_tracker/full_hydration_data.txt", "w", encoding="utf-8") as f:
            f.write(full_data_str)

        print("Combined hydration data and saved to full_hydration_data.txt")

    except FileNotFoundError:
        print("Error: hydration_data.json not found. Please run extract_hydration_data.py first.")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")

if __name__ == "__main__":
    combine_hydration_data()

