import re
import logging
import json
import demjson3
from bs4 import BeautifulSoup
from .json_parser_utils import find_product_with_offers_recursive, _find_product_data_recursive, extract_js_literal_from_push_string, remove_js_prefix, unescape_json_string


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


def robust_stateful_cleaner(data_string: str) -> str:
    """
    A state-aware parser to robustly clean the JSON-like data from BuyWisely.
    This approach is more resilient to changes in string content than regex replacements.
    """
    in_string = False
    is_escaped = False
    result = []
    
    i = 0
    while i < len(data_string):
        char = data_string[i]
        
        if in_string:
            if is_escaped:
                # The previous character was a backslash, so append this character literally
                result.append(char)
                is_escaped = False
            elif char == '\\':
                # This is an escape character, note it for the next iteration
                is_escaped = True
                result.append(char)
            elif char == '"':
                # We are leaving a string
                in_string = False
                result.append(char)
            else:
                # A regular character inside a string
                result.append(char)
        else:  # We are not in a string
            if char == '"':
                # We are entering a string
                in_string = True
                result.append(char)
            # Handle custom formats only when not in a string
            elif char == '$' and data_string[i:i+2] == '$D':
                # Match and wrap custom date objects like "$D2024-..." in quotes
                date_match = re.match(r'(\$D[\dTZ:.-]+)', data_string[i:])
                if date_match:
                    date_str = date_match.group(1)
                    result.append(f'"{date_str}"')
                    i += len(date_str) - 1  # Skip ahead
                else:
                    result.append(char)
            elif char == '<' and data_string[i:i+4] == '<$':
                # Match and replace React fragments like "<$L_..." with null
                fragment_match = re.match(r'(<\$L_[\w./]+>)', data_string[i:])
                if fragment_match:
                    fragment_str = fragment_match.group(1)
                    result.append('null')
                    i += len(fragment_str) - 1  # Skip ahead
                else:
                    result.append(char)
            else:
                # A regular character outside a string
                result.append(char)
        i += 1
        
    return "".join(result)


def _normalize_and_parse_push_block(block_content: str) -> dict | None:
    """
    Parses the content of a self.__next_f.push() call, which is a JS array literal.
    It decodes the array, extracts the data string if it contains product data,
    cleans it, and parses it.
    """
    _LOGGER.debug(f"[DIAG][hydration_parser] Processing push block (first 200): {block_content[:200]}")

    try:
        parsed_array = demjson3.decode(block_content)
    except demjson3.JSONDecodeError:
        try:
            cleaned_block = robust_stateful_cleaner(block_content)
            parsed_array = demjson3.decode(cleaned_block)
        except demjson3.JSONDecodeError as e:
            _LOGGER.warning(f"[DIAG][hydration_parser] Failed to decode push block after cleaning: {e}. Content: {block_content[:200]}")
            return None

    if not (isinstance(parsed_array, list) and len(parsed_array) > 1 and isinstance(parsed_array[1], str)):
        _LOGGER.debug("[DIAG][hydration_parser] Push block does not match expected [number, string] format.")
        return None

    data_string = parsed_array[1]

    if '"product"' not in data_string and '"offers"' not in data_string:
        _LOGGER.debug("[DIAG][hydration_parser] Skipping block without product/offers data.")
        return None

    _LOGGER.debug(f"[DIAG][hydration_parser] Found potential product data string (first 200): {data_string[:200]}")

    data_string = remove_js_prefix(data_string)
    cleaned_payload = robust_stateful_cleaner(data_string)

    _LOGGER.debug(f"[DIAG][hydration_parser] Cleaned payload (first 200): {cleaned_payload[:200]}")

    try:
        parsed_data = demjson3.decode(cleaned_payload)
        return parsed_data
    except demjson3.JSONDecodeError as e:
        _LOGGER.error(f"[DIAG][hydration_parser] Failed to parse product data payload: {e}")
        _LOGGER.error(f"[DIAG][hydration_parser] Problematic product payload (first 1000): {cleaned_payload[:1000]}")
        return None


def extract_and_parse_all_hydration_data(html: str) -> list:
    """
    Extracts and parses all Next.js hydration data from HTML.
    This version targets `self.__next_f.push()` calls and uses a robust
    manual parser to find the matching parentheses of the push() call.
    """
    _LOGGER.debug("[DIAG][hydration_parser] Starting extract_and_parse_all_hydration_data")

    soup = BeautifulSoup(html, 'html.parser')
    scripts = soup.find_all('script')
    
    start_str = 'self.__next_f.push('

    for script in scripts:
        if not script.string:
            continue

        content = script.string
        current_pos = 0
        
        while True:
            start_index = content.find(start_str, current_pos)
            if start_index == -1:
                break

            i = start_index + len(start_str)
            open_parens = 1
            in_string = False
            is_escaped = False

            while i < len(content) and open_parens > 0:
                char = content[i]
                
                if in_string:
                    if is_escaped:
                        is_escaped = False
                    elif char == '\\':
                        is_escaped = True
                    elif char == '"':
                        in_string = False
                else:
                    if char == '"':
                        in_string = True
                    elif char == '(':
                        open_parens += 1
                    elif char == ')':
                        open_parens -= 1
                i += 1
            
            if open_parens == 0:
                # The end of the push() call is at i-1. The content is between start_index + len(start_str) and i-1.
                block_content = content[start_index + len(start_str) : i - 1]
                _LOGGER.debug(f"[DIAG][hydration_parser] Found push block with balanced parens (length {len(block_content)}).")
                
                parsed_data = _normalize_and_parse_push_block(block_content)
                if parsed_data:
                    product_data = find_product_with_offers_recursive(parsed_data)
                    if product_data:
                        _LOGGER.info("[DIAG][hydration_parser] Found product data with offers in push block.")
                        # Normalize the 'title' key to 'name' to match the expected output format.
                        if 'title' in product_data:
                            product_data['name'] = product_data.pop('title')
                        return [product_data]
                
                current_pos = i
            else:
                _LOGGER.warning("[DIAG][hydration_parser] Could not find matching parenthesis for a push call, moving to next script.")
                break # Move to the next script tag
    
    _LOGGER.debug("[DIAG][hydration_parser] No product data found in any push blocks.")
    return []