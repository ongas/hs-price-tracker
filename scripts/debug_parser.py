import logging
import sys
import os
import json

# Add the project root to the Python path to allow importing custom_components
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from custom_components.price_tracker.services.buywisely.html_extractor import extract_product_data_from_html
from custom_components.price_tracker.services.buywisely.hydration_parser import extract_and_parse_all_hydration_data

# Configure logging to output to console
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
_LOGGER = logging.getLogger(__name__)

def main():
    html_file_path = "/mnt/e/source/personal_repos/homeassistant/custom_components/price_tracker/custom_components/price_tracker/temp_manually_saved_html.html"
    
    _LOGGER.info(f"Attempting to read HTML from: {html_file_path}")
    
    try:
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        _LOGGER.info(f"Successfully read HTML content. Length: {len(html_content)} characters.")
    except FileNotFoundError:
        _LOGGER.error(f"Error: File not found at {html_file_path}")
        return
    except Exception as e:
        _LOGGER.error(f"Error reading file {html_file_path}: {e}")
        return

    _LOGGER.info("Calling extract_and_parse_all_hydration_data directly...")
    try:
        parsed_hydration_data = extract_and_parse_all_hydration_data(html_content)
        _LOGGER.info(f"Result from extract_and_parse_all_hydration_data: {parsed_hydration_data}")
        if parsed_hydration_data:
            _LOGGER.info(f"Extracted product data: {json.dumps(parsed_hydration_data, indent=2)}")
        else:
            _LOGGER.warning("No product data extracted from hydration_parser.")
    except Exception as e:
        _LOGGER.error(f"Error during hydration parsing: {e}")

    _LOGGER.info("Calling extract_product_data_from_html (full extraction process)...")
    try:
        extracted_product_data = extract_product_data_from_html(html_content)
        _LOGGER.info(f"Result from extract_product_data_from_html: {extracted_product_data}")
        if extracted_product_data:
            _LOGGER.info(f"Full extracted product data: {json.dumps(extracted_product_data, indent=2)}")
        else:
            _LOGGER.warning("No product data extracted from full HTML extractor.")
    except Exception as e:
        _LOGGER.error(f"Error during full HTML extraction: {e}")

if __name__ == "__main__":
    main()