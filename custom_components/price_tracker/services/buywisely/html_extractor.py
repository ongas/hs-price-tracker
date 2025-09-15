import logging
import re
import json
from .nextjs_hydration_parser import NextJSHydrationDataExtractor

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

        def find_url_candidates(d):
            """Find all string fields in a dict that look like URLs."""
            candidates = []
            if isinstance(d, dict):
                for k, v in d.items():
                    if isinstance(v, str) and re.match(r'https?://', v):
                        candidates.append((k, v))
                    elif isinstance(v, dict):
                        candidates.extend(find_url_candidates(v))
                    elif isinstance(v, list):
                        for item in v:
                            candidates.extend(find_url_candidates(item))
            return candidates

        if product_data:
            _LOGGER.info(f"BuyWisely HtmlExtractor: Found product data: {product_data}")
            title = product_data.get('title')
            brand = title.split(' ')[0] if title else ''
            offers = product_data.get('offers', [])
            offers = offers[:10]

            # Find the offer with the lowest price
            def is_valid_seller_url(url):
                if not url or not isinstance(url, str):
                    return False
                url = url.strip()
                if re.search(r"\.(jpg|jpeg|png|gif|webp|svg|bmp|tiff)(\?|$)", url, re.IGNORECASE):
                    return False
                if product_data and url == product_data.get('image'):
                    return False
                if re.search(r"buywisely\.com\.au", url, re.IGNORECASE):
                    return False
                return url.startswith("http")

            lowest_offer = None
            lowest_price = None
            for offer in offers:
                price = offer.get('base_price')
                if price is not None:
                    try:
                        price_val = float(price)
                        if lowest_price is None or price_val < lowest_price:
                            lowest_price = price_val
                            lowest_offer = offer
                    except Exception:
                        continue

            main_url = ""
            if lowest_offer and is_valid_seller_url(lowest_offer.get('seller_product_url')):
                main_url = lowest_offer['seller_product_url']
                _LOGGER.info(f"[DIAG][html_extractor] Extracted seller_product_url from lowest-priced offer: {main_url}")
            else:
                _LOGGER.error("[html_extractor] No valid seller_product_url found in lowest-priced offer. Extraction failure.")

            raw_data = {
                'title': title,
                'price': product_data.get('lowest_price'),
                'image': product_data.get('image'),
                'currency': product_data.get('currency', 'AUD'),
                'availability': 'In Stock' if offers else 'Out of Stock',
                'brand': brand,
                'url': main_url,
                'offers': offers,
            }
            _LOGGER.info(f"[DIAG][html_extractor] raw_data['url'] set to: {main_url}")
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
                raw_data = {}
                if price_val is not None:
                    raw_data['price'] = price_val
                    raw_data['currency'] = 'AUD'
                    raw_data['availability'] = 'In Stock'
                    raw_data['brand'] = ''
                    raw_data['offers'] = []
                else:
                    raw_data['availability'] = 'Out of Stock'
                _LOGGER.info(f"BuyWisely HtmlExtractor: BeautifulSoup fallback extracted price: {price_val}")
            except Exception as e:
                _LOGGER.error(f"BuyWisely HtmlExtractor: BeautifulSoup fallback failed: {e}")
    except Exception as e:
        _LOGGER.error(f"BuyWisely HtmlExtractor: Error parsing with nextjs_hydration_parser: {e}")
    return raw_data