import importlib.util
import os
import logging

_LOGGER = logging.getLogger(__name__)


def _load_nextjs_extractor():
    module_name = "nextjs_hydration_parser"
    file_path = os.path.join(os.path.dirname(__file__), "nextjs_hydration_parser.py")
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec for {file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.NextJSHydrationDataExtractor

NextJSHydrationDataExtractor = _load_nextjs_extractor()

_LOGGER = logging.getLogger(__name__)

def extract_product_data_from_html(html: str) -> dict:
    """Extracts product data from BuyWisely HTML content."""
    _LOGGER.info("BuyWisely HtmlExtractor: Starting HTML extraction")
    extractor = NextJSHydrationDataExtractor()
    raw_data = {}
    product_data = None
    try:
        print("[DIAG][extract_product_data_from_html] HTML to parser:", html)
        parsed_data = extractor.parse(html)
        print(f"[DIAG][extract_product_data_from_html] parsed_data: {parsed_data}")
        for idx, item in enumerate(parsed_data):
            print(f"[DIAG][extract_product_data_from_html] parsed_data[{idx}]: type={type(item)}, keys={getattr(item, 'keys', lambda: [])() if hasattr(item, 'keys') else 'N/A'}")
        _LOGGER.info(f"BuyWisely HtmlExtractor: Parsed data from nextjs_hydration_parser: {parsed_data}")

        # Try legacy Next.js hydration format first
        for item in parsed_data:
            if isinstance(item, dict) and 'props' in item and 'pageProps' in item['props'] and 'product' in item['props']['pageProps']:
                product_data = item['props']['pageProps']['product']
                _LOGGER.info("BuyWisely HtmlExtractor: Found product data in legacy __NEXT_DATA__ format.")
                break

        # If not found, try new self.__next_f.push format
        if not product_data:
            for item in parsed_data:
                if isinstance(item, dict) and 'extracted_data' in item:
                    for ed in item['extracted_data']:
                        if 'data' in ed and isinstance(ed['data'], dict) and 'title' in ed['data']:
                            product_data = ed['data']
                            _LOGGER.info("BuyWisely HtmlExtractor: Found product data in self.__next_f.push format.")
                            break
                if product_data:
                    break

        if product_data:
            _LOGGER.info(f"BuyWisely HtmlExtractor: Found product data: {product_data}")
            title = product_data.get('title')
            slug = product_data.get('slug')
            extracted_url = product_data.get('url') # Get URL if it exists in product_data

            if extracted_url:
                vendor_url = extracted_url
                _LOGGER.info(f"BuyWisely HtmlExtractor: Extracted vendor_url directly: {vendor_url}")
            elif slug:
                # If only slug is available, construct a relative path or just use the slug
                # The full URL construction should ideally happen in data_transformer
                vendor_url = slug # Pass the slug as the URL for data_transformer to handle
                _LOGGER.info(f"BuyWisely HtmlExtractor: Using slug as vendor_url: {vendor_url}")
            else:
                vendor_url = None
                _LOGGER.info("BuyWisely HtmlExtractor: No slug or URL found in product data.")
            brand = title.split(' ')[0] if title else ''
            offers = product_data.get('offers', [])
            offers = offers[:10]
            _LOGGER.info(f"BuyWisely HtmlExtractor: Extracted {len(offers)} offers")
            raw_data = {
                'title': title,
                'price': product_data.get('lowest_price'),
                'image': product_data.get('image'),
                'currency': product_data.get('currency', 'AUD'),
                'availability': 'In Stock' if offers else 'Out of Stock',
                'brand': brand,
                'url': vendor_url,
                'offers': offers,
            }
        else:
            _LOGGER.info("BuyWisely HtmlExtractor: Product data not found in any supported hydration format.")
    except Exception as e:
        _LOGGER.error(f"BuyWisely HtmlExtractor: Error parsing with nextjs_hydration_parser: {e}")
    return raw_data