### Current Status Update:

**Completed Tasks:**
* Refactored `json_parser.py` into `json_extractor.py`, `json_parser_utils.py`, and `buywisely_hydration_parser.py`.
* Moved `_find_product_data_recursive` to `json_parser_utils.py` to resolve circular import.
* Corrected `re.sub` patterns in `buywisely_hydration_parser.py` for `\$D` dates and `\ references.
* Corrected `html_extractor.py` to properly assign `product_data` from `_find_product_data_recursive`.
* Broken down `test_buywisely_engine_parsing.py` into smaller test files (`test_basic_product_parsing.py`, `test_euro_currency_parsing.py`).
* Moved `is_valid_seller_url` from `html_extractor.py` to `json_parser_utils.py`.
* `ruff check --fix .` passes.
* Patched `html_extractor.py` and `data_transformer.py` to improve name extraction and fallback logic for BuyWisely products.
* Integrated the new, robust parsing logic from `scripts/debug_parser.py` into `custom_components/price_tracker/services/buywisely/buywisely_hydration_parser.py`.
* Removed a problematic regex substitution (`re.sub(r'T[a-zA-Z0-9]+,', '', final_string)`) from `buywisely_hydration_parser.py` that was causing JSON parsing errors.

**Current Issue:**
The `test_buywisely_parser.py::test_hydration_parser_with_real_data` test is currently failing. The `extract_and_parse_all_hydration_data` function is returning an empty list, indicating that the product data is not being extracted correctly from the provided HTML. Even with `tolerantjson` and its custom handlers, the parsing is failing with "Values must be separated by a comma" errors. This suggests that the JSON fragments within the `ref_map` values, after initial conversion by `_convert_i_identifier`, `_convert_hl_identifier`, and `_convert_e_identifier`, are still malformed.

**Requirements Gathered:**
*   **Strict adherence to "single line manipulation per function" rule:** Every distinct data manipulation must be encapsulated in its own helper function.
*   **Individual testability:** Each helper function should be individually testable.
*   **Correct data flow:** Functions must pass data in the correct format to subsequent steps.
*   **Robust JSON parsing:** The parser must correctly handle non-standard JSON-like strings from Next.js hydration data, including:
    *   Trailing commas
    *   Single-quoted strings
    *   Unquoted keys
    *   Extra tokens after valid JSON
    *   Escaped characters and malformed structures
    *   Next.js specific identifiers (`I[...]`, `HL[...]`, `E{...}`)
    *   References (`"$KEY"`, `"$LKEY"`)
*   **Use of `tolerantjson`:** Leverage `tolerantjson`'s capabilities, including custom handlers, for forgiving JSON parsing.
*   **`ruff check --fix` passes:** Maintain code quality and adherence to standards.
*   **All tests pass:** Ensure the new parser works correctly within the Home Assistant component and that all data fields are extracted and populated as expected.

**Next Steps:**
1.  **Refine `_convert_i_identifier`, `_convert_hl_identifier`, and `_convert_e_identifier` functions:** These functions need to be more robust. They should not just strip prefixes and wrap content, but also ensure that the *inner content* is valid JSON. This will involve attempting to parse the inner content using `tjson.tolerate` and then `json.dumps` the result to ensure canonical JSON. If `tjson.tolerate` fails, a fallback mechanism (e.g., quoting the string or wrapping in appropriate JSON structure) will be implemented.
2.  **End-to-End Testing:** Once the `test_hydration_parser_with_real_data` test passes, run all integration and unit tests to ensure the new parser works correctly within the Home Assistant component and that all data fields (`seller_product_url`, `name`, `price`, etc.) are extracted and populated as expected.
3.  **Code Cleanup:** Remove the temporary `scripts/debug_parser.py` script and any other debugging artifacts.
4.  **Final Verification:** Perform a final deployment and verification cycle to confirm the fix resolves the "UNKNOWN" product name issue and correctly populates the entity URL.