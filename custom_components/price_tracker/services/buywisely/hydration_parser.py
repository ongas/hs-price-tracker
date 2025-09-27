import re
import logging
import json
import demjson3
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
    # Diagnostic: print all script tags and their ids
    script_tags = soup.find_all('script')
    _LOGGER.info(f"[DIAG][NEXT_DATA] Found {len(script_tags)} <script> tags. IDs: {[tag.get('id') for tag in script_tags]}")
    for idx, tag in enumerate(script_tags):
        _LOGGER.info(f"[DIAG][NEXT_DATA] Script tag {idx}: id={tag.get('id')}, type={tag.get('type')}, first 100 chars: {str(tag)[:100]}")
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



# --- Robust stateful cleaner for push block normalization ---
def robust_stateful_cleaner(s: str) -> str:
    """
    Cleans a JSON-like string from a Next.js hydration push block using a state-aware approach.
    Handles string literals, escape sequences, $D date placeholders, and other quirks.
    """
    out = []
    i = 0
    in_str = False
    escape = False
    while i < len(s):
        c = s[i]
        if escape:
            out.append(c)
            escape = False
        elif c == '\\':
            out.append(c)
            escape = True
        elif c == '"':
            out.append(c)
            in_str = not in_str
        elif not in_str and s[i:i+2] == ':\"' and s[i+2:i+4] == '$,':
            # Remove ": \",$" patterns
            out.append(': ""')
            i += 3
        elif not in_str and s[i:i+3] == '"$D':
            # Replace "$D..." with "..."
            j = i+3
            while j < len(s) and s[j] != '"':
                j += 1
            out.append('"')
            out.append(s[i+3:j])
            out.append('"')
            i = j
        elif in_str and s[i:i+15] == '$Sreact.fragment':
            out.append('react.fragment')
            i += 14
        else:
            out.append(c)
        i += 1
    return ''.join(out)


def _find_balanced_json(s: str) -> str | None:
    """Finds a balanced JSON object string, ignoring braces within strings."""
    start_index = s.find('{')
    if start_index == -1:
        return None
    
    brace_count = 0
    in_string = False
    escape = False
    for i, char in enumerate(s[start_index:]):
        if escape:
            escape = False
            continue
        
        if char == '\\':
            escape = True
            continue

        if char == '"':
            in_string = not in_string

        if not in_string:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
        
        if brace_count == 0:
            return s[start_index : start_index + i + 1]
    return None


def _recursively_unescape_backslashes(s: str) -> str:
    """
    Recursively replaces double backslashes with single backslashes until no more double backslashes are found.
    This is to handle cases of over-escaping.
    """
    while '\\' in s:
        s = s.replace('\\', '__BACKSLASH_PLACEHOLDER__')
    s = s.replace('__BACKSLASH_PLACEHOLDER__', '\\')
    return s


from typing import Any
def _normalize_and_parse_push_block(block_content: str) -> Any | None:
    """
    Normalizes and parses a single push block content using robust_stateful_cleaner.
    """
    _LOGGER.debug(f"[DIAG][hydration_parser] Normalizing block content (first 500): {block_content[:500]}")

    # Extract the main string payload from the push block
    match = re.search(r'"\d+:(.*)"', block_content)
    if not match:
        _LOGGER.debug("[DIAG][hydration_parser] Could not find string literal with JSON in push block.")
        return None
    json_like_payload = match.group(1)
    _LOGGER.debug(f"[DIAG][hydration_parser] Extracted payload (first 500): {json_like_payload[:500]}")

    # Apply recursive unescaping for backslashes
    json_like_payload = _recursively_unescape_backslashes(json_like_payload)

    # Unescape quotes (only once, after recursive backslash unescaping)
    json_like_payload = json_like_payload.replace('"', '"')

    _LOGGER.debug(f"[DIAG][hydration_parser] Unescaped payload (first 500): {json_like_payload[:500]}")

    # Use robust stateful cleaner
    cleaned_payload = robust_stateful_cleaner(json_like_payload)

    # Find the balanced JSON object within the payload
    json_object_string = _find_balanced_json(cleaned_payload)

    if not json_object_string:
        _LOGGER.warning("[DIAG][hydration_parser] No balanced JSON object found in payload.")
        return None

    _LOGGER.debug(f"[DIAG][hydration_parser] Found balanced JSON object string (first 500): {json_object_string[:500]}")

    try:
        # Parse the object string using demjson3 for non-strict JSON
        parsed_data = demjson3.decode(json_object_string)
        return parsed_data
    except demjson3.JSONDecodeError as e:
        _LOGGER.error(f"[DIAG][hydration_parser] Failed to parse with demjson3: {e}")
        _LOGGER.error(f"[DIAG][hydration_parser] Problematic payload (first 1000): {json_object_string[:1000]}")
        return None


def extract_and_parse_all_hydration_data(html: str) -> list:
    """
    Extracts and parses all Next.js hydration data from HTML.
    This version targets `self.__next_f.push()` calls.
    """
    _LOGGER.debug("[DIAG][hydration_parser] Starting extract_and_parse_all_hydration_data")

    # 1. Try to extract from <script id='__NEXT_DATA__'> (legacy/SSR Next.js)
    results = []
    all_offers = []
    # 1. Extract from <script id='__NEXT_DATA__'> (legacy/SSR Next.js)
    next_data_objs = _extract_next_data_json(html)
    for obj in next_data_objs:
        product_data = find_product_with_offers_recursive(obj)
        if product_data:
            offers = product_data.get('offers')
            if isinstance(offers, list):
                pass  # placeholder for future aggregation logic

    # Find hydration blocks in <script> tags (including <head>)
    hydration_blocks = []
    soup = BeautifulSoup(html, "html.parser")
    hydration_data_parts = []
    for script in soup.find_all("script"):
        script_content = script.string or script.text or ""
        matches = re.findall(r'self\.__next_f\.push\(\[1,([\'\'])(.*?)\1\]\)', script_content, re.DOTALL)
        for _, part in matches:
            hydration_data_parts.append(part)

    if hydration_data_parts:
        full_block = "".join(hydration_data_parts)
        hydration_blocks.append(full_block)

    # Parse hydration blocks
    products = []
    for block in hydration_blocks:
        # Try to extract JSON from block, handling both quoted and unquoted JSON
        # Match '1:{...JSON...}' or '1:'{...JSON...}'
        json_match = re.search(r"1:([\"'])({.*})\1", block, re.DOTALL)
        if not json_match:
            json_match = re.search(r"1:({.*})", block, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                continue
        else:
            json_str = json_match.group(2)
        try:
            # Unescape any escaped quotes inside JSON
            json_str = json_str.replace('"', '"').replace("'", "'")
            data = demjson3.decode(json_str)
            _LOGGER.info(f"[DIAG][hydration_parser] Parsed hydration block: {json_str[:200]}")
            # Robustly access props/pageProps/product
            props = getattr(data, "props", None) or (data.get("props") if isinstance(data, dict) else {})
            pageProps = getattr(props, "pageProps", None) or (props.get("pageProps") if isinstance(props, dict) else {})
            product = getattr(pageProps, "product", None) or (pageProps.get("product") if isinstance(pageProps, dict) else {})
            if product:
                products.append(product)
        except Exception as e:
            _LOGGER.warning(f"[DIAG][hydration_parser] Failed to parse hydration block JSON: {e}")
    return products

    # Aggregate all offers into a single product dict if any offers found
    if all_offers:
        import pprint
        _LOGGER.info("[DIAG][hydration_parser] Aggregated offers (count=%d):\n%s", len(all_offers), pprint.pformat(all_offers))
        offers_with_price = [o for o in all_offers if isinstance(o, dict) and 'price' in o]
        # Try to merge product metadata from the first product_data found (if any)
        product_metadata = {}
        for pd in results:
            if isinstance(pd, dict):
                # Copy all fields except 'offers'
                for k, v in pd.items():
                    if k != 'offers':
                        product_metadata[k] = v
                break
        merged = dict(product_metadata)  # shallow copy
        merged['offers'] = offers_with_price if offers_with_price else all_offers
        _LOGGER.info(f"[DIAG][hydration_parser] Aggregated merged product: {merged}")
        return [merged]

    # If no results and no offers, return empty list (no fallback HTML parsing)
    return results