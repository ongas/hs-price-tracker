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
    soup = BeautifulSoup(html, 'html.parser')
    script = soup.find('script', id='__NEXT_DATA__')
    if script and script.get_text():
        try:
            data = json.loads(script.get_text())
            _LOGGER.info("[NEXT_DATA] Found and parsed <script id='__NEXT_DATA__'> JSON.")
            return [data]
        except Exception as e:
            _LOGGER.warning(f"[NEXT_DATA] Failed to parse <script id='__NEXT_DATA__'>: {e}")
    else:
        _LOGGER.info("[NEXT_DATA] No <script id='__NEXT_DATA__'> tag found.")
    return []


def _clean_date_placeholders(json_string: str) -> str:
    """Replaces $D date placeholders with properly formatted JSON date strings."""
    return re.sub(r'"\$D(.*?)"', r'"\1"', json_string)

def _clean_react_fragment_literal(json_string: str) -> str:
    """Replaces "$Sreact.fragment" literal with "react.fragment"."""
    return json_string.replace('"$Sreact.fragment"' , '"react.fragment"')

def _clean_dollar_comma_literal(json_string: str) -> str:
    """Removes "$,", which is not valid JSON."""
    # My fix: Replace : "$,", (with optional whitespace) with : ""
    return re.sub(r':\s*"\$,"', ': ""', json_string)


def extract_and_parse_all_hydration_data(html: str) -> list:
    """Extracts and parses all Next.js hydration data from HTML."""
    soup = BeautifulSoup(html, 'html.parser')

    # 1. Try to parse __NEXT_DATA__ script tag
    next_data_script = soup.find('script', {'id': '__NEXT_DATA__'})
    if next_data_script and next_data_script.string:
        try:
            next_data = json.loads(next_data_script.string)
            _LOGGER.debug(f"__NEXT_DATA__ successfully parsed: {next_data}")
            product_data = find_product_with_offers_recursive(_find_product_data_recursive(next_data))
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

    return []