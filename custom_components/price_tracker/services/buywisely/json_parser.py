import json
import logging
import re
from bs4 import BeautifulSoup
import demjson3

_LOGGER = logging.getLogger(__name__)

def find_product_data_in_html(html_content: str) -> list:
    """
    Parses the HTML to find all occurrences of Next.js hydration data,
    both from __NEXT_DATA__ and self.__next_f.push().
    It then searches for a dictionary containing an 'offers' list.
    """
    _LOGGER.debug("[DIAG][json_parser] Starting to find product data in HTML.")
    
    # List to store all found JSON objects
    all_json_objects = []

    # 1. Extract from <script id="__NEXT_DATA__">
    soup = BeautifulSoup(html_content, 'html.parser')
    next_data_script = soup.find('script', {'id': '__NEXT_DATA__'})
    if next_data_script and next_data_script.string:
        try:
            json_obj = json.loads(next_data_script.string)
            all_json_objects.append(json_obj)
            _LOGGER.debug("[DIAG][json_parser] Successfully parsed __NEXT_DATA__.")
        except json.JSONDecodeError as e:
            _LOGGER.warning(f"[DIAG][json_parser] Failed to parse __NEXT_DATA__: {e}")

    # 2. Extract from self.__next_f.push()
    push_matches = re.findall(r'self\.__next_f\.push\((.*?)\)', html_content, re.DOTALL)
    for match in push_matches:
        try:
            # demjson3 is used for its ability to handle less strict JSON
            json_obj = demjson3.decode(match)
            all_json_objects.append(json_obj)
            _LOGGER.debug(f"[DIAG][json_parser] Successfully parsed a self.__next_f.push() block.")
        except demjson3.JSONDecodeError:
            # If demjson3 fails, try to find JSON-like objects with regex
            json_like_objects = re.findall(r'(\{.*?\})', match)
            for obj_str in json_like_objects:
                try:
                    json_obj = json.loads(obj_str)
                    all_json_objects.append(json_obj)
                    _LOGGER.debug("[DIAG][json_parser] Successfully parsed a JSON-like object from a push block.")
                except json.JSONDecodeError:
                    continue

    # 3. Search for the product data with an 'offers' list in all found JSON objects
    _LOGGER.debug(f"[DIAG][json_parser] Searching for product data in {len(all_json_objects)} found JSON objects.")
    _LOGGER.debug(f"[DIAG][json_parser] all_json_objects: {all_json_objects}")
    for obj in all_json_objects:
        product_data = find_product_with_offers_recursive(obj)
        if product_data:
            _LOGGER.debug(f"[DIAG][json_parser] Found product data with offers: {product_data}")
            return [product_data] # Return as a list to maintain consistency

    _LOGGER.warning("[DIAG][json_parser] Could not find product data with an 'offers' list in any hydration block.")
    return []

def find_product_with_offers_recursive(data: any) -> dict | None:
    """
    Recursively searches for a dictionary that contains an 'offers' key,
    where 'offers' is a list of dictionaries, each with a 'seller_product_url'.
    """
    if isinstance(data, dict):
        _LOGGER.debug(f"[DIAG][json_parser] Checking dict with keys: {data.keys()}")
        # Check if the current dictionary contains a valid 'offers' list
        if 'offers' in data and isinstance(data['offers'], list):
            # Check if at least one offer has the required 'seller_product_url'
            if any(isinstance(offer, dict) and 'seller_product_url' in offer for offer in data['offers']):
                _LOGGER.debug(f"[DIAG][json_parser] Found valid 'offers' list in dictionary: {data}")
                return data
        
        # If not found, recurse into the values of the dictionary
        for value in data.values():
            found = find_product_with_offers_recursive(value)
            if found:
                return found
                
    elif isinstance(data, list):
        # If the data is a list, iterate over its items
        for item in data:
            found = find_product_with_offers_recursive(item)
            if found:
                return found
                
    return None

def extract_and_parse_all_hydration_data(html: str) -> list:
    """
    Main function to extract and parse all Next.js hydration data from HTML.
    This now wraps the new unified find_product_data_in_html function.
    """
    _LOGGER.debug("[DIAG][json_parser] Starting extraction and parsing of all hydration data.")
    results = find_product_data_in_html(html)
    _LOGGER.info(f"[DIAG][json_parser] Hydration parser found {len(results)} data object(s).")
    return results