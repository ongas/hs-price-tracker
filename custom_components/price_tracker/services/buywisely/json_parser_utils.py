import json
import logging
import re
import demjson3

_LOGGER = logging.getLogger(__name__)


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


def extract_js_literal_from_push_string(raw_push_string: str) -> str:
    """
    Extracts the core JavaScript literal string from a raw self.__next_f.push() string.
    """
    # The raw_push_string is typically of the form [1, "..."] or ["..."]
    # This regex captures the content after the first comma and inside the quotes.
    match = re.search(r'^\[\d+,\s*"(.*)"\]$', raw_push_string, re.DOTALL)
    if match:
        return match.group(1)
    return raw_push_string  # Return original if no match, though this shouldn't happen with valid input


def remove_js_prefix(js_literal_str: str) -> str:
    """
    Removes any leading 'XX:' prefix from a JavaScript literal string.
    """
    return re.sub(r"^[0-9a-fA-F]+:", "", js_literal_str)


def normalize_js_dates(js_str: str) -> str:
    """
    Replaces $D date placeholders with properly formatted JSON date strings.
    """
    # The regex patterns here should match the unescaped strings
    return re.sub(
        r'"\$D([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}Z)',
        r'"\1"',
        js_str,
    )


def resolve_js_references(js_str: str) -> str:
    """
    Replaces $ references (e.g., $34, $L59) with null.
    """
    return re.sub(r'"\$([0-9a-fA-F]+)"', r"null", js_str)


def unescape_json_string(json_str: str) -> str:
    """
    Unescapes backslashes in a JSON string (e.g., \" becomes ").
    """
    return json_str.replace('\\"', '"')


def parse_js_array_literal(js_str):
    """
    Parses a JavaScript-style array literal into a Python list.
    Handles single quotes, trailing commas, $D dates, and $ references.
    """
    # Step 1: Normalize quotes and booleans
    js_str = js_str.strip()
    js_str = js_str.replace("'", '"')  # Convert single to double quotes
    js_str = (
        js_str.replace("true", "true").replace("false", "false").replace("null", "null")
    )

    # Step 2: Remove trailing commas inside arrays or objects
    js_str = re.sub(r",\s*([\]}])", r"\\1", js_str)

    # Step 3: Decode escaped characters
    js_str = js_str.encode().decode("unicode_escape")

    # Step 4: Try parsing as JSON
    try:
        return json.loads(js_str)
    except json.JSONDecodeError as e:
        _LOGGER.warning(
            f"Failed to parse JS array literal with json.loads: {e}. Attempting with demjson3."
        )
        try:
            return demjson3.decode(js_str)
        except demjson3.JSONDecodeError as de:
            _LOGGER.error(
                f"Failed to parse JS array literal with demjson3: {de}. Original string: {js_str[:200]}..."
            )
            return None


def find_product_with_offers_recursive(data: any) -> dict | None:
    """
    Recursively searches for a dictionary that contains an 'offers' key,
    where 'offers' is a list of dictionaries, each with a 'seller_product_url'.
    """
    _LOGGER.debug(
        f"[DIAG][find_product_with_offers_recursive] Processing data (type: {type(data)}): {str(data)[:100]}..."
    )
    if isinstance(data, dict):
        if (
            "offers" in data
            and isinstance(data["offers"], list)
            and any(
                isinstance(o, dict) and "seller_product_url" in o
                for o in data["offers"]
            )
        ):
            _LOGGER.debug(
                f"[DIAG][find_product_with_offers_recursive] Found product data with offers: {str(data)[:100]}..."
            )
            return data
        for k, v in data.items():
            _LOGGER.debug(
                f"[DIAG][find_product_with_offers_recursive] Recursing into key '{k}'"
            )
            found = find_product_with_offers_recursive(v)
            if found:
                return found
    elif isinstance(data, list):
        _LOGGER.debug(
            f"[DIAG][find_product_with_offers_recursive] Iterating list of length {len(data)}"
        )
        for i, item in enumerate(data):
            _LOGGER.debug(
                f"[DIAG][find_product_with_offers_recursive] Recursing into list item {i}"
            )
            found = find_product_with_offers_recursive(item)
            if found:
                return found
    return None


def _find_product_data_recursive(data: any) -> dict | None:
    """
    Recursively searches for a dictionary that contains an 'offers' key,
    where 'offers' is a list of dictionaries, each with a 'seller_product_url'.
    """
    _LOGGER.debug(
        f"[DIAG][_find_product_data_recursive] Processing data (type: {type(data)}): {str(data)[:100]}..."
    )
    if isinstance(data, dict):
        if (
            "offers" in data
            and isinstance(data["offers"], list)
            and all(
                isinstance(o, dict) and "seller_product_url" in o
                for o in data["offers"]
            )
        ):
            _LOGGER.debug(
                f"[DIAG][_find_product_data_recursive] Found product data with offers: {str(data)[:100]}..."
            )
            return data
        for k, v in data.items():
            _LOGGER.debug(
                f"[DIAG][_find_product_data_recursive] Recursing into key '{k}'"
            )
            found = _find_product_data_recursive(v)
            if found:
                return found
    elif isinstance(data, list):
        _LOGGER.debug(
            f"[DIAG][_find_product_data_recursive] Iterating list of length {len(data)}"
        )
        for i, item in enumerate(data):
            _LOGGER.debug(
                f"[DIAG][_find_product_data_recursive] Recursing into list item {i}"
            )
            found = _find_product_data_recursive(item)
            if found:
                return found
    return None
