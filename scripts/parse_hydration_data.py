
import re
import json

def parse_hydration_data():
    """
    Parses the hydration data to extract the main product JSON object.
    """
    try:
        with open("/mnt/e/source/personal_repos/homeassistant/custom_components/price_tracker/full_hydration_data.txt", "r", encoding="utf-8") as f:
            full_data_str = f.read()

        # I'll look for a pattern that is more likely to be unique to the product data.
        # The product data seems to be in a dictionary with a "product" key.
        # I will try to extract the content of this dictionary.
        product_match = re.search(r'{\\"id\\":\\d+,\\"gid\\":\\"\\d+\\",\\"title\\":.*?\\"offers\\":.*?}]}}', full_data_str)

        if product_match:
            product_json_str = product_match.group(0)

            # Clean the string to make it valid JSON
            product_json_str = product_json_str.replace('\\"', '"') # Unescape quotes
            product_json_str = product_json_str.replace("\\n", "") # Remove newlines
            product_json_str = product_json_str.replace("\\", "") # Remove backslashes
            product_json_str = re.sub(r',(?=])', '', product_json_str) # Remove trailing commas in arrays

            try:
                product_json = json.loads(product_json_str)
                with open("/mnt/e/source/personal_repos/homeassistant/custom_components/price_tracker/final_hydration_data.json", "w", encoding="utf-8") as f:
                    json.dump(product_json, f, indent=2)
                print("Successfully parsed and saved final_hydration_data.json")
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                # Save the problematic string for debugging
                with open("/mnt/e/source/personal_repos/homeassistant/custom_components/price_tracker/problematic_json.txt", "w", encoding="utf-8") as f:
                    f.write(product_json_str)
                print("Saved problematic JSON string to problematic_json.txt")

        else:
            print("Could not find the product JSON object in the hydration data.")

    except FileNotFoundError:
        print("Error: full_hydration_data.txt not found. Please run combine_hydration_data.py first.")

if __name__ == "__main__":
    parse_hydration_data()
