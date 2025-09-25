
import re
import json

def clean_hydration_data():
    """
    Cleans the combined hydration data and extracts the main product JSON object.
    """
    try:
        with open("/mnt/e/source/personal_repos/homeassistant/custom_components/price_tracker/full_hydration_data.txt", "r", encoding="utf-8") as f:
            full_data_str = f.read()

        # This regex is designed to find the product object, which seems to start with
        # a specific structure.
        # I am looking for a json object that has the product title, and offers
        product_match = re.search(r'{"title":"Motorola Moto G75 5G 256GB Grey with Buds.*"offers":(.*)}', 
                              full_data_str)

        if product_match:
            product_json_str = product_match.group(0)

            # Further cleaning
            product_json_str = product_json_str.replace('\"', '"') # Unescape quotes
            product_json_str = product_json_str.replace("\n", "") # Remove newlines
            product_json_str = product_json_str.replace("\\", "") # Remove backslashes

            # It's still not perfect, but it's closer to valid JSON.
            # I will save this to a file for inspection.
            with open("/mnt/e/source/personal_repos/homeassistant/custom_components/price_tracker/cleaned_hydration_data.json", "w", encoding="utf-8") as f:
                f.write(product_json_str)

            print("Cleaned hydration data and saved to cleaned_hydration_data.json")
        else:
            print("Could not find the product JSON object in the hydration data.")

    except FileNotFoundError:
        print("Error: full_hydration_data.txt not found. Please run combine_hydration_data.py first.")

if __name__ == "__main__":
    clean_hydration_data()
