import re
import logging

import demjson3
from bs4 import BeautifulSoup
from .json_parser_utils import find_product_with_offers_recursive


_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.WARNING)


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
            elif char == "\\":
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
            elif char == "$" and data_string[i : i + 2] == "$D":
                # Match and wrap custom date objects like "$D2024-..." in quotes
                date_match = re.match(r"(\$D[\dTZ:.-]+)", data_string[i:])
                if date_match:
                    date_str = date_match.group(1)
                    result.append(f'"{date_str}"')
                    i += len(date_str) - 1  # Skip ahead
                else:
                    result.append(char)
            elif char == "<" and data_string[i : i + 4] == "<$":
                # Match and replace React fragments like "<$L_..." with null
                fragment_match = re.match(r"(<\$L_[\w./]+>)", data_string[i:])
                if fragment_match:
                    fragment_str = fragment_match.group(1)
                    result.append("null")
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
    # _LOGGER.debug(f"[DIAG][hydration_parser] Processing push block (first 200): {block_content[:200]}")

    # Log raw block content for diagnostics
    # _LOGGER.debug(f"[DIAG][hydration_parser] Raw push block (first 200): {block_content[:200]}")

    # Try to parse as JS array literal

    # Try demjson3 first
    try:
        parsed_array_literal = demjson3.decode(block_content)
    # _LOGGER.debug("[DIAG][hydration_parser] demjson3 successfully parsed array literal.")
    except demjson3.JSONDecodeError as e:
        _LOGGER.warning(
            f"[DIAG][hydration_parser] demjson3 failed for array literal: {e}. Attempting enhanced manual extraction. Content: {block_content[:200]}"
        )
        arr_match = re.match(r"^\s*\[(.*)\]\s*$", block_content, re.DOTALL)
        elements = []
        if arr_match:
            arr_content = arr_match.group(1)
            depth = 0
            current = []
            in_string = False
            is_escaped = False
            for c in arr_content:
                if in_string:
                    if is_escaped:
                        is_escaped = False
                    elif c == "\\":
                        is_escaped = True
                    elif c == '"':
                        in_string = False
                    current.append(c)
                else:
                    if c == '"':
                        in_string = True
                        current.append(c)
                    elif c in "{[":
                        depth += 1
                        current.append(c)
                    elif c in "}]":
                        depth -= 1
                        current.append(c)
                    elif c == "," and depth == 0:
                        elements.append("".join(current).strip())
                        current = []
                    else:
                        current.append(c)
            if current:
                elements.append("".join(current).strip())
            # Try all elements for product/offers
            for idx, elem in enumerate(elements):
                cleaned = robust_stateful_cleaner(elem)
                try:
                    payload = demjson3.decode(cleaned)
                    found_product = find_product_with_offers_recursive(payload)
                    if found_product:
                        # _LOGGER.info(f"[DIAG][hydration_parser] Found product with offers in element {idx}.")
                        return found_product
                except Exception as e2:
                    _LOGGER.warning(
                        f"[DIAG][hydration_parser] Failed to parse element {idx}: {e2}. Content: {elem[:200]}"
                    )
                # NEW: Try to parse string elements as JSON if they look like object literals
                if elem.startswith('"') and "{" in elem:
                    try:
                        possible_json = elem.strip('"')
                        possible_json_cleaned = robust_stateful_cleaner(possible_json)
                        payload = demjson3.decode(possible_json_cleaned)
                        found_product = find_product_with_offers_recursive(payload)
                        if found_product:
                            # _LOGGER.info(f"[DIAG][hydration_parser] Found product with offers in string element {idx}.")
                            return found_product
                    except Exception as e3:
                        _LOGGER.warning(
                            f"[DIAG][hydration_parser] Failed to parse string element {idx}: {e3}. Content: {elem[:200]}"
                        )
                else:
                    pass  # Skipped string element
            _LOGGER.error(
                f"[DIAG][hydration_parser] No product with offers found in any top-level or string element. Elements: {elements}"
            )
            return None
        else:
            _LOGGER.error(
                f"[DIAG][hydration_parser] Could not match array literal format for manual extraction. Content: {block_content[:200]}"
            )
            return None
    except Exception as e:
        _LOGGER.warning(
            f"[DIAG][hydration_parser] Unexpected error: {e}. Content: {block_content[:200]}"
        )
        return None

    # Find the first dictionary in the array (skip any string elements)
    product_payload = None

    def extract_object_literals_from_string(s):
        # Robust stateful parser to extract the largest balanced {...} block containing 'offers'
        max_obj = None
        max_obj_len = 0
        i = 0
        while i < len(s):
            if s[i] == "{":
                depth = 1
                start = i
                in_string = False
                is_escaped = False
                j = i + 1
                while j < len(s) and depth > 0:
                    c = s[j]
                    if in_string:
                        if is_escaped:
                            is_escaped = False
                        elif c == "\\":
                            is_escaped = True
                        elif c == '"':
                            in_string = False
                    else:
                        if c == '"':
                            in_string = True
                        elif c == "{":
                            depth += 1
                        elif c == "}":
                            depth -= 1
                    j += 1
                if depth == 0:
                    obj_str = s[start:j]
                    if "offers" in obj_str and len(obj_str) > max_obj_len:
                        max_obj = obj_str
                        max_obj_len = len(obj_str)
                i = j
            else:
                i += 1
        if max_obj:
            # _LOGGER.info(f"[DIAG][hydration_parser] Extracted largest object literal containing 'offers' (length {max_obj_len}): {max_obj[:200]}")
            return [max_obj]
        else:
            # _LOGGER.info("[DIAG][hydration_parser] No object literal containing 'offers' found in string block.")
            return []

    if isinstance(parsed_array_literal, list):
        for item in parsed_array_literal:
            if isinstance(item, dict):
                product_payload = item
                break
            # Try to parse string elements as JSON if they look like object literals
            if isinstance(item, str) and "{" in item:
                # Extract all object literals from the string
                object_literals = extract_object_literals_from_string(item)
                for obj_str in object_literals:
                    try:
                        possible_json_cleaned = robust_stateful_cleaner(obj_str)
                        payload = demjson3.decode(possible_json_cleaned)
                        found_product = find_product_with_offers_recursive(payload)
                        if found_product:
                            # _LOGGER.info(f"[DIAG][hydration_parser] Found product with offers in extracted object literal from string item.")
                            # _LOGGER.info(f"[DIAG][hydration_parser] Extracted object literal: {obj_str[:200]}")
                            return found_product
                    except Exception as e3:
                        _LOGGER.warning(
                            f"[DIAG][hydration_parser] Failed to parse extracted object literal: {e3}. Content: {obj_str[:200]}"
                        )
    elif isinstance(parsed_array_literal, dict):
        product_payload = parsed_array_literal

    if product_payload is None:
        # _LOGGER.debug("[DIAG][hydration_parser] No dictionary found in push block to process.")
        return None

    found_product = find_product_with_offers_recursive(product_payload)
    if found_product:
        return found_product
    return product_payload


def extract_and_parse_all_hydration_data(html: str) -> list:
    """
    Extracts and parses all Next.js hydration data from HTML.
    This version targets `self.__next_f.push()` calls and uses a robust
    manual parser to find the matching parentheses of the push() call.
    """
    # _LOGGER.debug("[DIAG][hydration_parser] Starting extract_and_parse_all_hydration_data")

    soup = BeautifulSoup(html, "html.parser")
    scripts = soup.find_all("script")

    extracted_data = []

    start_str = "self.__next_f.push("

    for script in scripts:
        if not script.string:
            continue

        content = script.string
        # if content:
        #     _LOGGER.debug(f"[DIAG][hydration_parser] script.string length: {len(content)}")
        # else:
        #     _LOGGER.debug("[DIAG][hydration_parser] script.string is empty.")
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
                    elif char == "\\":
                        is_escaped = True
                    elif char == '"':
                        in_string = False
                else:
                    if char == '"':
                        in_string = True
                    elif char == "(":
                        open_parens += 1
                    elif char == ")":
                        open_parens -= 1
                i += 1

            if open_parens == 0:
                # The end of the push() call is at i-1. The content is between start_index + len(start_str) and i-1.
                block_content = content[start_index + len(start_str) : i - 1]
                # _LOGGER.debug(f"[DIAG][hydration_parser] Extracted block_content length: {len(block_content)}.")
                # _LOGGER.debug(f"[DIAG][hydration_parser] Found push block with balanced parens (length {len(block_content)}).")

                parsed_data = _normalize_and_parse_push_block(block_content)
                if parsed_data:
                    product_data = find_product_with_offers_recursive(parsed_data)
                    if product_data:
                        # _LOGGER.info("[DIAG][hydration_parser] Found product data with offers in push block.")
                        # if 'offers' in product_data:
                        #     _LOGGER.info(f"[DIAG][hydration_parser] Raw offers list: {demjson3.encode(product_data['offers'], compactly=False, indent=2)}")
                        # else:
                        #     _LOGGER.info("[DIAG][hydration_parser] No 'offers' key found in product data.")
                        # Normalize the 'title' key to 'name' to match the expected output format.
                        if "title" in product_data:
                            product_data["name"] = product_data.pop("title")
                        extracted_data.append(product_data)

                current_pos = i
            else:
                _LOGGER.warning(
                    "[DIAG][hydration_parser] Could not find matching parenthesis for a push call, moving to next script."
                )
                break  # Move to the next script tag

    if extracted_data:
        return extracted_data

    # _LOGGER.debug("[DIAG][hydration_parser] No product data found in any push blocks.")
    return []
