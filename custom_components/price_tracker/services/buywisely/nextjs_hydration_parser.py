import json
import logging
import re
import pprint # Keep pprint for debugging purposes, can be removed later
import tolerantjson as tjson

_LOGGER = logging.getLogger(__name__)

def _unescape_double_quotes(text: str) -> str:
    """Unescapes double quotes in a string."""
    return text.replace('"', '"')

def _unescape_newlines(text: str) -> str:
    """Unescapes newlines in a string."""
    return text.replace('\\n', '\n')

def _unescape_quotes_and_newlines(chunk: str) -> str:
    """Unescapes double quotes and newlines in a string chunk."""
    chunk = _unescape_double_quotes(chunk)
    chunk = _unescape_newlines(chunk)
    return chunk

def _replace_date_format(text: str) -> str:
    """Replaces $D date format with just the date string."""
    return re.sub(r'"\$D([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}Z)"', r'"\1"', text)

def _replace_react_fragment_string(text: str) -> str:
    """Replaces $Sreact.fragment with react.fragment."""
    return text.replace('"\$Sreact.fragment"', '"react.fragment"')

def _remove_dollar_comma(text: str) -> str:
    """Removes '$",' from the string."""
    return text.replace('"$",', '')

def _wrap_in_json_array(content: str) -> str:
    """Wraps content in JSON array brackets."""
    return f"[{content}]"

def _convert_i_identifier(text: str) -> str:
    """Converts I[...] identifier to its inner content as a JSON array, ensuring inner content is valid JSON."""
    def replace_i(match):
        inner_content = match.group(1)
        try:
            # Attempt to parse the inner content as JSON
            parsed_content = tjson.tolerate(inner_content)
            # If successful, dump it back to a canonical JSON string
            return _wrap_in_json_array(json.dumps(parsed_content))
        except Exception:
            # If parsing fails, treat the inner content as a string literal
            _LOGGER.debug(f"Failed to parse I[...] inner content as JSON: {inner_content[:100]}...")
            return _wrap_in_json_array(json.dumps(inner_content))
    return re.sub(r'I\[(.*?)\]', replace_i, text)

def _convert_hl_identifier(text: str) -> str:
    """Converts HL[...] identifier to its inner content as a JSON array, ensuring inner content is valid JSON."""
    def replace_hl(match):
        inner_content = match.group(1)
        try:
            # Attempt to parse the inner content as JSON
            parsed_content = tjson.tolerate(inner_content)
            # If successful, dump it back to a canonical JSON string
            return _wrap_in_json_array(json.dumps(parsed_content))
        except Exception:
            # If parsing fails, treat the inner content as a string literal
            _LOGGER.debug(f"Failed to parse HL[...] inner content as JSON: {inner_content[:100]}...")
            return _wrap_in_json_array(json.dumps(inner_content))
    return re.sub(r'HL\[(.*?)\]', replace_hl, text)

def _convert_e_identifier(text: str) -> str:
    """Converts E{...} identifier to its inner content as a JSON object, ensuring inner content is valid JSON."""
    def replace_e(match):
        inner_content = match.group(1)
        try:
            # Attempt to parse the inner content as JSON
            parsed_content = tjson.tolerate(f"{{{inner_content}}}") # Wrap in braces to make it a valid object
            # If successful, dump it back to a canonical JSON string
            return json.dumps(parsed_content)
        except Exception:
            # If parsing fails, treat the inner content as a string literal within an object
            _LOGGER.debug(f"Failed to parse E{{...}} inner content as JSON: {inner_content[:100]}...")
            # Fallback: return a JSON object with a string value
            return json.dumps({"_malformed_e_content": inner_content})
    return re.sub(r'E\{(.*?)\}', replace_e, text)

def _split_content_into_lines(content: str) -> list[str]:
    """Splits content into lines."""
    return content.splitlines()

def _extract_payload_chunk_start(line: str) -> int:
    """Finds the start index of the payload chunk in a line."""
    return line.find('"')

def _extract_payload_chunk_end(line: str) -> int:
    """Finds the end index of the payload chunk in a line."""
    return line.rfind('"')

def _get_payload_chunk_from_line(line: str, start: int, end: int) -> str:
    """Extracts the payload chunk from a line given start and end indices."""
    return line[start+1:end]

def _join_and_unescape_payload_chunks(payload_chunks: list[str]) -> str:
    """Joins payload chunks and unescapes quotes and newlines."""
    return "".join(_unescape_quotes_and_newlines(chunk) for chunk in payload_chunks)


def _compile_record_regex() -> re.Pattern:
    """Compiles the regex for matching records."""
    return re.compile(r'^([a-zA-Z0-9]+):(.*)')

def _match_record_regex(record_regex: re.Pattern, record: str) -> re.Match | None:
    """Matches a record against the record regex."""
    return record_regex.match(record)

def _get_match_group_1(match: re.Match) -> str:
    """Gets the first group from a regex match."""
    return match.group(1)

def _get_match_group_2(match: re.Match) -> str:
    """Gets the second group from a regex match."""
    return match.group(2)

def _format_key_as_string_literal(key: str) -> str:
    """Formats a key as a JSON string literal."""
    return f'"{key}"'

def _get_recursion_guard_placeholder() -> str:
    """Returns the recursion guard placeholder string."""
    return '__RECURSION_GUARD__'

def _get_value_from_ref_map(key: str, ref_map: dict) -> str:
    """Retrieves a value from the reference map."""
    return ref_map[key]

def _find_references_in_value(value: str) -> list[str]:
    """Finds all '$' and '$L' references in a string value."""
    return re.findall(r'"\$L?([a-zA-Z0-9]+)"', value)

def _sort_references_by_length(refs: list[str]) -> list[str]:
    """Sorts a list of references by length in reverse order."""
    return sorted(list(set(refs)), key=len, reverse=True)

def _replace_reference_in_value(value: str, ref_key: str, resolved_value: str) -> str:
    """Replaces a '$' reference in a string value with its resolved value."""
    return value.replace(f'"\${ref_key}"', resolved_value)

def _update_resolved_cache(resolved_cache: dict, key: str, value: str) -> None:
    """Updates the resolved cache with a key-value pair."""
    resolved_cache[key] = value

def _check_main_product_record_exists(ref_map: dict) -> bool:
    """Checks if the main product record (key '11') exists in the ref_map."""
    return '11' in ref_map



def _decode_json_with_tolerantjson(text: str, ref_map: dict) -> any:
    """Decodes a JSON string using tolerantjson with custom handlers for references."""
    def resolve_tjson_reference(key: str):
        # This handler will be called by tolerantjson when it encounters a '$KEY' or '$LKEY'
        # It needs to return the actual value for that key from the ref_map.
        # If the key is not found, return a placeholder or raise an error.
        if key in ref_map:
            return ref_map[key]
        _LOGGER.warning(f"Reference key '{key}' not found in ref_map during tolerantjson parsing.")
        return None # Or raise an error, depending on desired behavior

    return tjson.tolerate(text, custom_handlers={
        '$': resolve_tjson_reference,
        '$L': resolve_tjson_reference # Use the same handler for $L references
    })

def _find_product_data(decoded_data: any) -> dict:
    """Finds product data recursively within decoded data."""
    from .json_parser_utils import _find_product_data_recursive
    return _find_product_data_recursive(decoded_data)


def build_ref_map(content: str) -> dict:
    """Builds a reference map from the raw Next.js hydration data."""
    lines = _split_content_into_lines(content)
    payload_chunks = []
    for line in lines:
        if line.startswith('self.__next_f.push([1,'):
            # Extract the string content within the push array
            # The format is typically self.__next_f.push([1,"..."})
            # We need to extract the "..." part
            start = _extract_payload_chunk_start(line)
            end = _extract_payload_chunk_end(line)
            if start != -1 and end != -1 and start != end:
                payload_chunks.append(_get_payload_chunk_from_line(line, start, end))

            full_payload = _join_and_unescape_payload_chunks(payload_chunks)


    records = _split_content_into_lines(full_payload)
    ref_map = {}
    record_regex = _compile_record_regex()

    for record in records:
        match = _match_record_regex(record_regex, record)
        if match:
            # Apply custom identifier conversions here, before storing in ref_map
            value = match.group(2)
            value = _convert_i_identifier(value)
            value = _convert_hl_identifier(value)
            value = _convert_e_identifier(value)
            ref_map[_get_match_group_1(match)] = value
    return ref_map



def extract_and_parse_all_hydration_data(html_content: str) -> list[dict]:
    """
    Extracts and parses all Next.js hydration data from HTML.
    """
    ref_map = build_ref_map(html_content)
    
    if not _check_main_product_record_exists(ref_map):
        _LOGGER.warning("Error: Main product record (key '11') not found in ref_map.")
        return []

    _LOGGER.debug("--- Resolving All References ---")
    # resolved_cache is no longer needed as tolerantjson handles recursion
    # final_string is now directly passed to tolerantjson
    final_string_to_parse = ref_map['11'] # Get the main product record from ref_map

    # Final cleanup steps as per debug_parser.py and status_update.md
    # These are still needed as tolerantjson might not handle all string replacements
    final_string_to_parse = _replace_date_format(final_string_to_parse)
    final_string_to_parse = _replace_react_fragment_string(final_string_to_parse)
    final_string_to_parse = _remove_dollar_comma(final_string_to_parse)

    _LOGGER.debug(f"--- Final String before JSON decode (first 500 chars) ---\n{final_string_to_parse[:500]}")

    try:
        # Pass ref_map to the decoding function for custom handlers
        decoded_data = _decode_json_with_tolerantjson(final_string_to_parse, ref_map)
        _LOGGER.debug("Successfully decoded final string with tolerantjson.")
    except Exception as e: # Catch a broader exception as tolerantjson might raise different errors
        _LOGGER.error(f"Failed to decode final string with tolerantjson: {e}")
        _LOGGER.error(f"Problematic string (first 500 chars): {final_string_to_parse[:500]}")
        return []

    # Now, recursively find the product data within the decoded_data
    product_data = _find_product_data(decoded_data)

    if product_data:
        _LOGGER.debug("--- Final Parsed Product Data ---")
        _LOGGER.debug(pprint.pformat(product_data))
        return [product_data]
    else:
        _LOGGER.warning("Could not find product data in the decoded hydration data.")
        return []