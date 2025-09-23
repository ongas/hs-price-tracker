
import re
import logging
import json
from bs4 import BeautifulSoup
from .json_parser_utils import find_product_with_offers_recursive

from demjson3 import decode
from custom_components.price_tracker.services.buywisely.hydration_helpers import robust_identifier_conversion

_LOGGER = logging.getLogger(__name__)

def _extract_raw_next_f_push_strings(html: str) -> list[str]:
    """
    Extracts raw strings from self.__next_f.push() calls within script tags.
    """
    _LOGGER.debug(f"[_extract_raw_next_f_push_strings] Input HTML or raw: {html[:200]}...")
    payload_chunks = []
    soup = BeautifulSoup(html, 'html.parser')
    script_tags = soup.find_all('script')
    if script_tags:
        for idx, script in enumerate(script_tags):
            script_text = script.get_text() if script else ''
            _LOGGER.debug(f"[_extract_raw_next_f_push_strings] Processing <script> tag #{idx}, length={len(script_text) if script_text else 0}")
            if script_text:
                for line in script_text.splitlines():
                    if line.strip().startswith('self.__next_f.push([1,'):
                        _LOGGER.debug(f"[_extract_raw_next_f_push_strings] Found matching line: {line[:200]}...")
                        start = line.find('"')
                        end = line.rfind('"')
                        if start != -1 and end != -1 and start != end:
                            payload_chunks.append(line[start+1:end])
                            _LOGGER.debug(f"[_extract_raw_next_f_push_strings] Appended payload chunk: {line[start+1:end][:200]}...")
    else:
        # Fallback: treat input as plain hydration string, extract lines directly
        _LOGGER.info("No <script> tags found, treating input as plain hydration string.")
        for line in html.splitlines():
            if line.startswith('self.__next_f.push([1,'):
                _LOGGER.debug(f"[_extract_raw_next_f_push_strings] Fallback found matching line: {line[:200]}...")
                start = line.find('"')
                end = line.rfind('"')
                if start != -1 and end != -1 and start != end:
                    payload_chunks.append(line[start+1:end])
                    _LOGGER.debug(f"[_extract_raw_next_f_push_strings] Fallback appended payload chunk: {line[start+1:end][:200]}...")
    _LOGGER.debug(f"[_extract_raw_next_f_push_strings] Final payload_chunks: {payload_chunks}")
    return payload_chunks

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


def build_ref_map(html: str) -> dict:
    """Builds a reference map from the raw Next.js hydration data in the HTML, using robust tolerantjson parsing for identifiers."""
    payload_chunks = _extract_raw_next_f_push_strings(html)
    full_payload = '\n'.join(payload_chunks)
    full_payload = full_payload.replace('\\"', '"').replace('\\n', '\n')
    records = full_payload.splitlines()
    ref_map = {}
    record_regex = re.compile(r'^([a-zA-Z0-9]+):(.*)')
    for record in records:
        match = record_regex.match(record)
        if match:
            # Use robust identifier conversion for the value
            value = robust_identifier_conversion(match.group(2))
            # Always store as string for downstream processing
            if not isinstance(value, str):
                try:
                    value = json.dumps(value, ensure_ascii=False)
                except Exception:
                    value = str(value)
            ref_map[match.group(1)] = value
    return ref_map


def resolve_recursive(key, ref_map, resolved_cache):
    """Recursively resolves a reference key."""
    if key in resolved_cache:
        return resolved_cache[key]
    if key not in ref_map:
        return f'"${key}"'

    resolved_cache[key] = '"__RECURSION_GUARD__"'
    value = ref_map[key]
    # Ensure value is always a string for regex and replace
    if not isinstance(value, str):
        try:
            value = json.dumps(value, ensure_ascii=False)
        except Exception:
            value = str(value)
    refs = re.findall(r'"\$([a-zA-Z0-9]+)"', value)
    for ref_key in set(refs):
        resolved_value = resolve_recursive(ref_key, ref_map, resolved_cache)
        # Ensure resolved_value is string
        if not isinstance(resolved_value, str):
            try:
                resolved_value = json.dumps(resolved_value, ensure_ascii=False)
            except Exception:
                resolved_value = str(resolved_value)
        value = value.replace(f'"${ref_key}"', resolved_value)

    resolved_cache[key] = value
    return value

def _clean_date_placeholders(json_string: str) -> str:
    """Replaces $D date placeholders with properly formatted JSON date strings."""
    return re.sub(r'"\$D(.*?)"', r'"\1"', json_string)

def _clean_react_fragment_literal(json_string: str) -> str:
    """Replaces "$Sreact.fragment" literal with "react.fragment"."""
    return json_string.replace('"$Sreact.fragment"' , '"react.fragment"')

def _clean_dollar_comma_literal(json_string: str) -> str:
    """Replaces any value field containing only "$," with an empty string value."""
    # Replace : "$," (with optional whitespace) with : ""
    return re.sub(r':\s*"\$,"', ': ""', json_string)

def extract_and_parse_all_hydration_data(html: str) -> list:
    """Extracts and parses all Next.js hydration data from HTML."""
    # First, try to extract from <script id="__NEXT_DATA__"> if present
    next_data_results = _extract_next_data_json(html)
    results = []

    if next_data_results:
        _LOGGER.info(f"[NEXT_DATA] Extracted {len(next_data_results)} JSON object(s) from <script id='__NEXT_DATA__'>.")
        # Patch: robust recursive extraction for deeply nested product dicts with offers
        def collect_all_product_dicts_with_offers(data):
            found = []
            if isinstance(data, dict):
                # If this dict has a non-empty 'offers' list, collect it and do not descend further
                offers = data.get('offers')
                if isinstance(offers, list) and len(offers) > 0 and all(isinstance(o, dict) for o in offers):
                    found.append(data)
                else:
                    # Otherwise, descend into all values
                    for v in data.values():
                        found.extend(collect_all_product_dicts_with_offers(v))
            elif isinstance(data, list):
                for item in data:
                    found.extend(collect_all_product_dicts_with_offers(item))
            return found

        for obj in next_data_results:
            product_dicts = collect_all_product_dicts_with_offers(obj)
            for product_data in product_dicts:
                offers = product_data.get('offers', [])
                if not offers:
                    _LOGGER.warning(f"[NEXT_DATA] Skipping product_data with empty offers: {str(product_data)[:200]}...")
                    continue
                for offer in offers:
                    if isinstance(offer, dict):
                        if 'base_price' not in offer:
                            offer['base_price'] = offer.get('price')
                        if 'seller_product_url' not in offer:
                            offer['seller_product_url'] = None
                _LOGGER.info(f"[NEXT_DATA] Appending product_data: {str(product_data)[:200]}...")
                results.append(product_data)
        if results:
            _LOGGER.info(f"Hydration parser found {len(results)} product data object(s) from <script id='__NEXT_DATA__'>.")
            return results
        else:
            _LOGGER.info("[NEXT_DATA] No product data found in <script id='__NEXT_DATA__'> JSON.")

    # Fallback to legacy Next.js hydration extraction
    ref_map = build_ref_map(html)
    if not ref_map:
        _LOGGER.info("No hydration reference map could be built.")
        return []

    resolved_cache = {}
    for key in ref_map.keys():
        resolve_recursive(key, ref_map, resolved_cache)
    _LOGGER.info(f"[DIAG] resolved_cache: {resolved_cache}")
    for key, resolved_string in resolved_cache.items():
        _LOGGER.debug(f"[DIAG] Resolved string for key {key}: {resolved_string[:500]}...")
        if any(x in resolved_string for x in ['product', 'offers', 'title', 'seller_product_url']):
            try:
                cleaned_step1 = _clean_date_placeholders(resolved_string)
                cleaned_step2 = _clean_react_fragment_literal(cleaned_step1)
                final_string = _clean_dollar_comma_literal(cleaned_step2)
                parsed_json = decode(final_string)
                _LOGGER.info(f"[DIAG] Parsed JSON from resolved string: {parsed_json}")
                product_data = find_product_with_offers_recursive(parsed_json)
                if not product_data:
                    if isinstance(parsed_json, dict) and 'product' in parsed_json:
                        product_candidate = parsed_json['product']
                        if isinstance(product_candidate, dict) and 'offers' in product_candidate:
                            product_data = product_candidate
                if not product_data:
                    if isinstance(parsed_json, dict) and 'title' in parsed_json and 'offers' in parsed_json:
                        product_data = parsed_json
                if not product_data:
                    if isinstance(parsed_json, dict) and 'offers' in parsed_json:
                        product_data = parsed_json
                if product_data:
                    _LOGGER.info(f"[DIAG] Appending product_data: {str(product_data)[:200]}...")
                    results.append(product_data)
            except Exception as e:
                _LOGGER.warning(f"Could not parse resolved record {key}: {e}")
    _LOGGER.info(f"Hydration parser found {len(results)} product data object(s) (legacy fallback).")
    return results