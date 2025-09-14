import logging
import re
import json
from nextjs_hydration_parser import NextJSHydrationDataExtractor

_LOGGER = logging.getLogger(__name__)


def _find_product_data_recursive(data):
    if isinstance(data, dict):
        if 'product' in data and isinstance(data['product'], dict):
            return data['product']
        for key, value in data.items():
            result = _find_product_data_recursive(value)
            if result:
                return result
    elif isinstance(data, list):
        for item in data:
            result = _find_product_data_recursive(item)
            if result:
                return result
    return None

def extract_product_data_from_html(html: str) -> dict:
    """Extracts product data from BuyWisely HTML content."""
    _LOGGER.info("BuyWisely HtmlExtractor: Starting HTML extraction")
    extractor = NextJSHydrationDataExtractor()
    raw_data = {}
    product_data = None
    try:
        _LOGGER.info(f"[DIAG] Raw HTML length: {len(html)}")
        parsed_data = extractor.parse(html)
        _LOGGER.info(f"[DIAG] Parsed data from nextjs_hydration_parser: {parsed_data}")

        # If parsed_data is empty or not as expected, fallback to manual extraction
        if not parsed_data or (isinstance(parsed_data, list) and not parsed_data):
            _LOGGER.warning("[DIAG] NextJSHydrationDataExtractor returned empty, attempting manual __NEXT_DATA__ extraction.")
            match = re.search(r'<script[^>]*id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>', html, re.DOTALL)
            if match:
                try:
                    next_data_json = match.group(1)
                    parsed_data = json.loads(next_data_json)
                    _LOGGER.info(f"[DIAG] Manually extracted __NEXT_DATA__ JSON: {type(parsed_data)}")
                except Exception as e:
                    _LOGGER.error(f"[DIAG] Failed to parse __NEXT_DATA__ JSON: {e}")
                    parsed_data = {}

        # If parsed_data is a dict and has 'props'->'pageProps'->'product', use that (as in test HTML)
        product_data = None
        if isinstance(parsed_data, dict):
            product_data = parsed_data.get('props', {}).get('pageProps', {}).get('product')
        # If not found, try the original specific path for list structure
        if not product_data and isinstance(parsed_data, list):
            try:
                if len(parsed_data) > 0 and \
                   isinstance(parsed_data[0], dict) and 'extracted_data' in parsed_data[0] and \
                   isinstance(parsed_data[0]['extracted_data'], list) and len(parsed_data[0]['extracted_data']) > 0 and \
                   isinstance(parsed_data[0]['extracted_data'][0], dict) and 'data' in parsed_data[0]['extracted_data'][0] and \
                   isinstance(parsed_data[0]['extracted_data'][0]['data'], list) and len(parsed_data[0]['extracted_data'][0]['data']) > 0 and \
                   isinstance(parsed_data[0]['extracted_data'][0]['data'][0], list) and len(parsed_data[0]['extracted_data'][0]['data'][0]) > 3 and \
                   isinstance(parsed_data[0]['extracted_data'][0]['data'][0][3], dict) and 'product' in parsed_data[0]['extracted_data'][0]['data'][0][3]:
                    product_data = parsed_data[0]['extracted_data'][0]['data'][0][3]['product']
                    _LOGGER.info("BuyWisely HtmlExtractor: Found product data at specific nested path.")
            except (IndexError, KeyError, TypeError) as e:
                _LOGGER.debug(f"BuyWisely HtmlExtractor: Product data not found at specific nested path: {e}")
                product_data = None
        # Fallback to recursive search if not found at specific path
        if not product_data:
            product_data = _find_product_data_recursive(parsed_data)

        if product_data:
            _LOGGER.info(f"BuyWisely HtmlExtractor: Found product data: {product_data}")
            title = product_data.get('title')
            slug = product_data.get('slug')
            extracted_url = product_data.get('url') # Get URL if it exists in product_data

            if extracted_url:
                vendor_url = extracted_url
                _LOGGER.info(f"BuyWisely HtmlExtractor: Extracted vendor_url directly: {vendor_url}")
            elif slug:
                vendor_url = slug
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
            _LOGGER.info("BuyWisely HtmlExtractor: Product data not found in any supported hydration format. Trying BeautifulSoup fallback.")
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html, 'html.parser')
                price_text = None
                price_elem = soup.find(class_="price")
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                price_val = None
                if price_text:
                    match = re.search(r"([\d,.]+)", price_text.replace(",", ""))
                    if match:
                        price_val = float(match.group(1))
                raw_data = {
                    'title': None,
                    'price': price_val,
                    'image': None,
                    'currency': 'AUD',
                    'availability': 'In Stock' if price_val is not None else 'Out of Stock',
                    'brand': '',
                    'url': None,
                    'offers': [],
                }
                _LOGGER.info(f"BuyWisely HtmlExtractor: BeautifulSoup fallback extracted price: {price_val}")
            except Exception as e:
                _LOGGER.error(f"BuyWisely HtmlExtractor: BeautifulSoup fallback failed: {e}")
    except Exception as e:
        _LOGGER.error(f"BuyWisely HtmlExtractor: Error parsing with nextjs_hydration_parser: {e}")
    return raw_data