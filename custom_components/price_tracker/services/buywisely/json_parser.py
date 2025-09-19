
import json
import logging
import re
from bs4 import BeautifulSoup
import demjson3

_LOGGER = logging.getLogger(__name__)

def extract_next_data_json_string(html: str) -> str | None:
    """
    Extracts the JSON string from <script id="__NEXT_DATA__"> tag.
    """
    soup = BeautifulSoup(html, 'html.parser')
    next_data_script = soup.find('script', {'id': '__NEXT_DATA__'})
    if next_data_script and next_data_script.string:
        return next_data_script.string
    return None

def extract_next_f_push_json_strings(html: str) -> list[str]:
    """
    Extracts JSON strings from self.__next_f.push() calls.
    """
    soup = BeautifulSoup(html, 'html.parser')
    json_strings = []
    for script in soup.find_all('script'):
        if script.string and 'self.__next_f.push' in script.string:
            matches = re.findall(r'self\.__next_f\.push\((.*?)\)', script.string, re.DOTALL)
            for match in matches:
                json_strings.append(match)
    return json_strings

def parse_json_string_robustly(json_str: str) -> dict | list | None:
    """
    Parses a JSON string using demjson3 first, then falls back to standard json.
    """
    try:
        data = demjson3.decode(json_str)
        _LOGGER.debug("Successfully parsed with demjson3.")
        return data
    except demjson3.JSONDecodeError as e:
        _LOGGER.warning(f"demjson3 failed to parse, trying standard json: {e}")
        try:
            data = json.loads(json_str)
            _LOGGER.debug("Successfully parsed with standard json.")
            return data
        except json.JSONDecodeError as json_err:
            _LOGGER.error(f"Failed to parse with both demjson3 and json: {json_err}")
            return None

def extract_and_parse_all_hydration_data(html: str) -> list:
    """
    Extracts and parses all Next.js hydration data from HTML.
    """
    results = []

    # Handle __NEXT_DATA__
    next_data_str = extract_next_data_json_string(html)
    if next_data_str:
        parsed_data = parse_json_string_robustly(next_data_str)
        if parsed_data:
            results.append(parsed_data)

    # Handle self.__next_f.push()
    next_f_push_strings = extract_next_f_push_json_strings(html)
    for json_str in next_f_push_strings:
        # For self.__next_f.push, the match is typically a list-like string, e.g., '[1, "33:{...}"]'
        # We need to parse this outer list first, then extract the inner JSON string.
        outer_parsed = parse_json_string_robustly(json_str)
        if outer_parsed and isinstance(outer_parsed, list) and len(outer_parsed) > 1 and isinstance(outer_parsed[1], str) and ':' in outer_parsed[1]:
            chunk_id, inner_json_str = outer_parsed[1].split(':', 1)
            inner_parsed = parse_json_string_robustly(inner_json_str)
            if inner_parsed:
                results.append({
                    'chunk_id': str(outer_parsed[0]),
                    'extracted_data': [{
                        'type': 'colon_separated',
                        'identifier': chunk_id,
                        'data': inner_parsed
                    }],
                })
        elif outer_parsed: # If it's a valid JSON but not in the expected format, still include it
            results.append(outer_parsed)

    _LOGGER.info(f"Hydration parser found {len(results)} data object(s).")
    return results
