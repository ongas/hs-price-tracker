import sys
import os
import json
import logging

# Configure logging to output debug messages to stderr
logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)
_LOGGER = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('/mnt/e/source/personal_repos/homeassistant/custom_components/price_tracker'))

from custom_components.price_tracker.services.buywisely.buywisely_hydration_parser import extract_and_parse_all_hydration_data  # noqa: E402

# Define the path to the HTML file
HTML_FILE_PATH = '/mnt/e/source/personal_repos/homeassistant/custom_components/price_tracker/custom_components/price_tracker/temp_fetched_html.html'

try:
    with open(HTML_FILE_PATH, 'r', encoding='utf-8') as f:
        html_content = f.read()
except FileNotFoundError:
    _LOGGER.error(f"Error: HTML file not found at {HTML_FILE_PATH}")
    sys.exit(1)
except Exception as e:
    _LOGGER.error(f"Error reading HTML file: {e}")
    sys.exit(1)

# Extract and parse all hydration data
parsed_data_list = extract_and_parse_all_hydration_data(html_content)

# Print the extracted data
if parsed_data_list:
    for item in parsed_data_list:
        print(json.dumps(item, indent=2))
else:
    _LOGGER.info("No hydration data found or extraction failed.")
