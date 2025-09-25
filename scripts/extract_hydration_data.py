
import re
import json
from bs4 import BeautifulSoup

def extract_hydration_data():
    """
    Extracts hydration data from the fetched HTML and saves it to a file.
    """
    try:
        with open("/mnt/e/source/personal_repos/homeassistant/custom_components/price_tracker/custom_components/price_tracker/temp_fetched_html.html", "r", encoding="utf-8") as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, 'html.parser')
        
        hydration_data = []
        
        # Find all script tags
        script_tags = soup.find_all('script')
        
        for script in script_tags:
            if script.string and 'self.__next_f.push' in script.string:
                # Extract the content inside self.__next_f.push()
                match = re.search(r'self\.__next_f\.push\((.*?)\)', script.string, re.DOTALL)
                if match:
                    # The content is a list, but might be represented as a string
                    # Let's try to parse it
                    try:
                        # This is a bit of a hack, as it's not valid JSON
                        # We'll try to make it valid
                        json_string = match.group(1)
                        
                        # It's not perfect, but it's a start
                        hydration_data.append(json_string)
                    except (json.JSONDecodeError, TypeError):
                        # If it fails, just append the raw string
                        hydration_data.append(match.group(1))

        with open("/mnt/e/source/personal_repos/homeassistant/custom_components/price_tracker/hydration_data.json", "w", encoding="utf-8") as f:
            json.dump(hydration_data, f, indent=2)
            
        print("Hydration data extracted and saved to hydration_data.json")

    except FileNotFoundError:
        print("Error: temp_fetched_html.html not found. Please run fetch_buywisely_html.py first.")

if __name__ == "__main__":
    extract_hydration_data()
