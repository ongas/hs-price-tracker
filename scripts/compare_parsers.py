import time
import json
from custom_components.price_tracker.utilities.hydration_parser import parse_nextjs_hydration_data as new_parser
from hydration_parser import NextJSHydrationDataExtractor
from custom_components.price_tracker.services.buywisely.html_extractor import extract_product_data_from_html

import logging

HTML_FILE = "scripts/fetched_html_content_0.html"

logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger("custom_components.price_tracker.services.buywisely.html_extractor")
_LOGGER.setLevel(logging.DEBUG)

def compare_parsers():
    """Compares the performance and output of the old and new hydration parsers."""
    with open(HTML_FILE, "r") as f:
        html_content = f.read()

    # --- Old Parser ---
    old_parser_instance = NextJSHydrationDataExtractor()
    def old_parser_func(html):
        return old_parser_instance.parse(html)

    start_time = time.time()
    old_result = extract_product_data_from_html(html_content, parser_func=old_parser_func)
    old_time = time.time() - start_time

    # --- New Parser ---
    start_time = time.time()
    new_result = extract_product_data_from_html(html_content, parser_func=new_parser)
    new_time = time.time() - start_time

    # --- Comparison ---
    print("--- Parser Comparison ---")
    print(f"Old Parser Time: {old_time:.6f} seconds")
    print(f"New Parser Time: {new_time:.6f} seconds")

    print("\n--- Old Parser Final Price ---")
    print(old_result.get('price'))

    print("\n--- New Parser Raw Output ---")
    print("\n--- New Parser Raw Output (before JSON dump) ---")
    print(new_result)

    print("\n--- New Parser Raw Output (before JSON dump) ---")
    print(new_result)

    with open("new_parser_output.json", "w") as f:
        json.dump(new_result, f, indent=2, default=str)

    print("\n--- New Parser Final Price ---")
    print(new_result.get('price'))

if __name__ == "__main__":
    compare_parsers()