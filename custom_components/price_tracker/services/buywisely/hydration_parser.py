import re
import logging
from bs4 import BeautifulSoup
from .json_parser_utils import find_product_with_offers_recursive

from demjson3 import decode
from custom_components.price_tracker.services.buywisely.hydration_helpers import robust_identifier_conversion

_LOGGER = logging.getLogger(__name__)

def _extract_raw_next_f_push_strings(html: str) -> list[str]:
    """
    Extracts raw strings from self.__next_f.push() calls within script tags.
    """
    _LOGGER.debug(f"[_extract_raw_next_f_push_strings] Input HTML: {html[:200]}...")
    soup = BeautifulSoup(html, 'html.parser')
    payload_chunks = []
    for script in soup.find_all('script'):
        _LOGGER.debug(f"[_extract_raw_next_f_push_strings] Found script tag: {script}")
        if script.string:
            _LOGGER.debug(f"[_extract_raw_next_f_push_strings] Script string: {script.string[:200]}...")
            for line in script.string.splitlines():
                if line.startswith('self.__next_f.push([1,'):
                    _LOGGER.debug(f"[_extract_raw_next_f_push_strings] Found matching line: {line[:200]}...")
                    start = line.find('"')
                    end = line.rfind('"')
                    if start != -1 and end != -1 and start != end:
                        payload_chunks.append(line[start+1:end])
                        _LOGGER.debug(f"[_extract_raw_next_f_push_strings] Appended payload chunk: {line[start+1:end][:200]}...")
    _LOGGER.debug(f"[_extract_raw_next_f_push_strings] Final payload_chunks: {payload_chunks}")
    return payload_chunks


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
            ref_map[match.group(1)] = robust_identifier_conversion(match.group(2))
    return ref_map


def resolve_recursive(key, ref_map, resolved_cache):
    """Recursively resolves a reference key."""
    if key in resolved_cache:
        return resolved_cache[key]
    if key not in ref_map:
        return f'"${key}"'

    resolved_cache[key] = '"__RECURSION_GUARD__"'
    value = ref_map[key]
    
    refs = re.findall(r'"\$([a-zA-Z0-9]+)"', value)
    for ref_key in set(refs):
        resolved_value = resolve_recursive(ref_key, ref_map, resolved_cache)
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
    """Removes "$," literal."""
    return json_string.replace('"$,"', '')

def extract_and_parse_all_hydration_data(html: str) -> list:
    """Extracts and parses all Next.js hydration data from HTML."""
    ref_map = build_ref_map(html)
    
    if not ref_map:
        _LOGGER.info("No hydration reference map could be built.")
        return []

    resolved_cache = {}
    for key in ref_map.keys():
        resolve_recursive(key, ref_map, resolved_cache)
    
    _LOGGER.info(f"[DIAG] resolved_cache: {resolved_cache}")
    
    results = []
    for key, resolved_string in resolved_cache.items():
        _LOGGER.debug(f"[DIAG] Resolved string for key {key}: {resolved_string[:500]}...")
        if 'product' in resolved_string or 'offers' in resolved_string: # Simplified condition
            try:
                # Apply cleanup steps sequentially
                cleaned_step1 = _clean_date_placeholders(resolved_string)
                cleaned_step2 = _clean_react_fragment_literal(cleaned_step1)
                final_string = _clean_dollar_comma_literal(cleaned_step2)

                # Attempt to parse the entire string as JSON
                parsed_json = decode(final_string)
                _LOGGER.info(f"[DIAG] Parsed JSON from resolved string: {parsed_json}")

                product_data = find_product_with_offers_recursive(parsed_json)
                if product_data:
                    results.append(product_data)

            except Exception as e:
                _LOGGER.warning(f"Could not parse resolved record {key}: {e}")

    _LOGGER.info(f"Hydration parser found {len(results)} product data object(s).")
    return results