import re
import logging
import json
from bs4 import BeautifulSoup
from .json_parser_utils import find_product_with_offers_recursive, _find_product_data_recursive


_LOGGER = logging.getLogger(__name__)


def _extract_next_data_json(html: str) -> list[dict]:
    """
    Extracts and parses JSON from <script id="__NEXT_DATA__"> tags if present.
    Returns a list of parsed JSON objects (may be empty).
    """
    # This function is currently unused in extract_and_parse_all_hydration_data,
    # but keeping it for completeness. The logic below will be more robust.
    soup = BeautifulSoup(html, 'html.parser')
    script = soup.find('script', id='__NEXT_DATA__')
    if script and script.string:
        try:
            data = json.loads(script.string)
            _LOGGER.info("[NEXT_DATA] Found and parsed <script id='__NEXT_DATA__'> JSON.")
            return [data]
        except Exception as e:
            _LOGGER.warning(f"[NEXT_DATA] Failed to parse <script id='__NEXT_DATA__'>: {e}")
    else:
        _LOGGER.info("[NEXT_DATA] No <script id='__NEXT_DATA__'> tag found.")
    return []


def _clean_date_placeholders(json_string: str) -> str:
    """
    Replaces $D date placeholders with properly formatted JSON date strings.
    """
    return re.sub(r'"\$D(.*?)"', r'"\1"', json_string)


def _clean_react_fragment_literal(json_string: str) -> str:
    """
    Replaces "$Sreact.fragment" literal with "react.fragment".
    """
    return json_string.replace('"$Sreact.fragment"' , '"react.fragment"')


def _clean_dollar_comma_literal(json_string: str) -> str:
    """
    Removes "$,", which is not valid JSON.
    """
    # My fix: Replace : "$,", (with optional whitespace) with : ""
    return re.sub(r':\s*"\$,"', ': ""', json_string)


def extract_and_parse_all_hydration_data(html: str) -> list:
    """
    Extracts and parses all Next.js hydration data from HTML.
    """
    _LOGGER.debug("[DIAG][hydration_parser] Starting extract_and_parse_all_hydration_data")

    # Use regex to find the __NEXT_DATA__ script tag content
    match = re.search(r'<script[^>]*id=["\\]?__NEXT_DATA__["\\]?[^>]*>(.*?)</script>', html, re.DOTALL)
    
    if match:
        next_data_json_string = match.group(1)
        _LOGGER.debug(f"[DIAG][hydration_parser] __NEXT_DATA__ script tag content found via regex. Length: {len(next_data_json_string)} chars.")
        _LOGGER.debug(f"[DIAG][hydration_parser] __NEXT_DATA__ content (first 500 chars): {next_data_json_string[:500]}")

        try:
            next_data = json.loads(next_data_json_string)
            _LOGGER.debug(f"[DIAG][hydration_parser] __NEXT_DATA__ json.loads successful. Type: {type(next_data)}")
            _LOGGER.debug(f"[DIAG][hydration_parser] __NEXT_DATA__ parsed data (first 500 chars): {str(next_data)[:500]}")

            product_data_recursive_search = _find_product_data_recursive(next_data)
            _LOGGER.debug(f"[DIAG][hydration_parser] Result of _find_product_data_recursive: {product_data_recursive_search}")

            product_data = find_product_with_offers_recursive(product_data_recursive_search)
            _LOGGER.debug(f"[DIAG][hydration_parser] Result of find_product_with_offers_recursive: {product_data}")

            if product_data:
                _LOGGER.info("Found product data from __NEXT_DATA__.")
                return [product_data]
            else:
                _LOGGER.info("No product data found in __NEXT_DATA__.")
                return []
        except json.JSONDecodeError as e:
            _LOGGER.warning(f"Failed to parse __NEXT_DATA__ as JSON: {e}")
        except Exception as e:
            _LOGGER.warning(f"Error processing __NEXT_DATA__: {e}")
    else:
        _LOGGER.debug("[DIAG][hydration_parser] __NEXT_DATA__ script tag not found via regex.")

    _LOGGER.debug("[DIAG][hydration_parser] Returning empty list.")
    return []