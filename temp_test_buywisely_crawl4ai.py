"""
Temporary script to test the buywisely service using crawl4ai feature.
"""

import sys
import asyncio
import traceback
import os

print("Script entry.", flush=True)
try:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'custom_components', 'price_tracker')))
    from services.buywisely import BuyWiselyEngine
    print("Imported BuyWiselyEngine successfully.", flush=True)
except Exception as import_error:
    print(f"Import error: {import_error}", flush=True)
    traceback.print_exc()
    sys.exit(1)

PRODUCT_URL = "https://buywisely.com.au/product/motorola-moto-g75-5g-256gb-grey-with-buds"

async def test_buywisely_crawl4ai():
    print(f"Testing crawl4ai for: {PRODUCT_URL}", flush=True)
    try:
        engine = BuyWiselyEngine(extraction_method="advanced")
        print("Engine instantiated.", flush=True)
        result = await engine.get_product_details(PRODUCT_URL)
        print("Test completed. Output:", flush=True)
        print(result, flush=True)
        if not result:
            print("No result returned. Check service implementation or network connectivity.", flush=True)
    except Exception as e:
        print(f"An error occurred during test execution: {e}", flush=True)
        traceback.print_exc()

if __name__ == "__main__":
    print("Starting buywisely crawl4ai test...", flush=True)
    asyncio.run(test_buywisely_crawl4ai())
    print("Script execution finished.", flush=True)
