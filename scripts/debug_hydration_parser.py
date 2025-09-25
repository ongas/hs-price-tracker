

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import re
import logging
import json
import demjson3
from bs4 import BeautifulSoup

from custom_components.price_tracker.services.buywisely import json_parser_utils

_LOGGER = logging.getLogger(__name__)

def debug_hydration_parser():
    """
    Debugs the hydration parsing process using temp_fetched_html.html.
    """
    try:
        with open("/mnt/e/source/personal_repos/homeassistant/custom_components/price_tracker/custom_components/price_tracker/temp_fetched_html.html", "r", encoding="utf-8") as f:
            html_content = f.read()

        product_dicts = []

        # Try to parse the __NEXT_DATA__ script tag first
        match = re.search(r'<script[^>]*id=["\\]?__NEXT_DATA__["\\]?[^>]*>(.*?)</script>', html_content, re.DOTALL)
        if match:
            next_data_json_string = match.group(1)
            try:
                next_data = json.loads(next_data_json_string)
                product_data = json_parser_utils._find_product_data_recursive(next_data)
                if product_data:
                    product_dicts.append(product_data)
                    _LOGGER.info("Found product data from __NEXT_DATA__.")
            except (json.JSONDecodeError, TypeError) as e:
                _LOGGER.warning(f"Failed to parse __NEXT_DATA__ as JSON: {e}")

        # If no product data found yet, try self.__next_f.push() blocks
        if not product_dicts:
            push_pattern = re.compile(r"self\.__next_f\.push\((.*?)\);", re.DOTALL)
            push_matches = push_pattern.findall(html_content)

            for idx, payload in enumerate(push_matches):
                _LOGGER.debug(f"Processing push block #{idx+1}")
                print(f"Raw payload (first 500 chars): {payload[:500]}") # Added print
                try:
                    # Apply cleaning steps from json_parser_utils
                    cleaned = json_parser_utils.unescape_json_string(payload)
                    cleaned = json_parser_utils._clean_date_placeholders(cleaned)
                    cleaned = json_parser_utils._clean_react_fragment_literal(cleaned)
                    cleaned = json_parser_utils._clean_dollar_comma_literal(cleaned)
                    
                    _LOGGER.debug(f"Cleaned payload (first 500 chars): {cleaned[:500]}")
                    print(f"Attempting to parse: {cleaned}") # Added print statement

                    try:
                        parsed_obj = json_parser_utils.parse_js_array_literal(cleaned)
                    except demjson3.JSONDecodeError as e:
                        _LOGGER.error(f"Failed to parse with demjson3: {e}. Problematic string: {cleaned[:500]}...")
                        parsed_obj = None

                    if parsed_obj is not None:
                        _LOGGER.debug(f"Parsed object from push block #{idx+1}: {str(parsed_obj)[:500]}")
                        product_data = json_parser_utils.find_product_with_offers_recursive(parsed_obj)
                        if product_data:
                            product_dicts.append(product_data)
                            _LOGGER.info(f"Found product data in push block #{idx+1}.")
                    else:
                        _LOGGER.warning(f"parse_js_array_literal returned None for push block #{idx+1}.")

                except Exception as e:
                    _LOGGER.error(f"Error processing push block #{idx+1}: {e}")

        if product_dicts:
            print("Successfully extracted product data:")
            for product in product_dicts:
                print(json.dumps(product, indent=2))
        else:
            print("No product data could be extracted.")

    except FileNotFoundError:
        print("Error: temp_fetched_html.html not found. Please run fetch_buywisely_html.py first.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG) # Set logging level to DEBUG
    debug_hydration_parser()

