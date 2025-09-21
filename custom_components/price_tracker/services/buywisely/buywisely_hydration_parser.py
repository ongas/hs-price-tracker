import logging
from custom_components.price_tracker.services.buywisely.json_extractor import extract_next_data_json_string, extract_next_f_push_json_strings
from custom_components.price_tracker.services.buywisely.json_parser_utils import parse_json_string_robustly, find_product_with_offers_recursive, extract_js_literal_from_push_string, remove_js_prefix, normalize_js_dates, resolve_js_references, unescape_json_string, _find_product_data_recursive

_LOGGER = logging.getLogger(__name__)

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
            # Recursively search for product data within this parsed structure using _find_product_data_recursive
            product_data = _find_product_data_recursive(parsed_data)
            if product_data:
                results.append(product_data)

    # Handle self.__next_f.push()
    next_f_push_strings = extract_next_f_push_json_strings(html)
    for raw_push_string in next_f_push_strings:
        _LOGGER.debug(f"[DIAG][buywisely_hydration_parser] Processing raw push string: {raw_push_string[:100]}...")

        # Step 1: Extract the core JavaScript literal string
        js_literal_str = extract_js_literal_from_push_string(raw_push_string)
        _LOGGER.debug(f"[DIAG][buywisely_hydration_parser] Extracted JS literal string: {js_literal_str[:100]}...")

        # Step 2: Remove the XX: prefix
        no_prefix_js_str = remove_js_prefix(js_literal_str)
        _LOGGER.debug(f"[DIAG][buywisely_hydration_parser] After removing prefix: {no_prefix_js_str[:100]}...")

        # Step 3: Handle $D date placeholders
        normalized_dates_js_str = normalize_js_dates(no_prefix_js_str)
        _LOGGER.debug(f"[DIAG][buywisely_hydration_parser] After normalizing dates: {normalized_dates_js_str[:100]}...")

        # Step 4: Handle $ references (replace with null for now)
        resolved_references_js_str = resolve_js_references(normalized_dates_js_str)
        _LOGGER.debug(f"[DIAG][buywisely_hydration_parser] After resolving references: {resolved_references_js_str[:100]}...")

        # Step 5: Unescape backslashes (if any remain from original string)
        final_json_str = unescape_json_string(resolved_references_js_str)
        _LOGGER.debug(f"[DIAG][buywisely_hydration_parser] Final JSON string for parsing: {final_json_str[:100]}...")

        # Attempt to parse the final string as JSON
        parsed_payload = parse_json_string_robustly(final_json_str)
        _LOGGER.debug(f"[DIAG][buywisely_hydration_parser] Parsed payload: {parsed_payload}")

        if parsed_payload:
            # Recursively search for product data within this parsed structure
            product_data = find_product_with_offers_recursive(parsed_payload)
            _LOGGER.debug(f"[DIAG][buywisely_hydration_parser] Result of find_product_with_offers_recursive: {product_data}")
            if product_data:
                results.append(product_data)

    _LOGGER.info(f"Hydration parser found {len(results)} data object(s).")
    return results