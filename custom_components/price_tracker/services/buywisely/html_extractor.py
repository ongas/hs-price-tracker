import logging
import re
import json
from custom_components.price_tracker.utilities.hydration_parser import parse_nextjs_hydration_data

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
    raw_data = {}
    product_data = None
    try:
        _LOGGER.info(f"[DIAG] Raw HTML length: {len(html)}")
        parsed_data = parse_nextjs_hydration_data(html)
        # Deep diagnostics: log the entire parsed_data (hydration data)
        try:
            import json as _json
            _LOGGER.info(f"[DIAG][html_extractor] Full parsed_data (hydration): { _json.dumps(parsed_data, default=str)[:10000] }")
        except Exception as e:
            _LOGGER.error(f"[DIAG][html_extractor] Exception logging full parsed_data: {e}")
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

        # Robustly traverse hydration data to find the product dict with offers
        product_data = None
        def find_product_with_offers(data):
            """Recursively search for a dict with an 'offers' key containing a list of dicts with 'seller_product_url'."""
            if isinstance(data, dict):
                if 'offers' in data and isinstance(data['offers'], list) and any(isinstance(o, dict) and 'seller_product_url' in o for o in data['offers']):
                    return data
                for v in data.values():
                    found = find_product_with_offers(v)
                    if found:
                        return found
            elif isinstance(data, list):
                for item in data:
                    found = find_product_with_offers(item)
                    if found:
                        return found
            return None

        # Try direct dict path (legacy/test)
        if isinstance(parsed_data, dict):
            product_data = parsed_data.get('props', {}).get('pageProps', {}).get('product')
        # If not found or doesn't have offers, search recursively for offers
        if not (product_data and isinstance(product_data, dict) and 'offers' in product_data and isinstance(product_data['offers'], list) and product_data['offers']):
            product_data = find_product_with_offers(parsed_data)
        # Fallback to original recursive search if still not found
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
            # Deep diagnostics: log the full offers list and all candidate seller_product_url values
            try:
                all_seller_urls = [offer.get('seller_product_url') for offer in offers if 'seller_product_url' in offer]
                _LOGGER.info(f"[DIAG][html_extractor] Full offers list: {offers}")
                _LOGGER.info(f"[DIAG][html_extractor] All candidate seller_product_url values: {all_seller_urls}")
            except Exception as e:
                _LOGGER.error(f"[DIAG][html_extractor] Exception logging offers diagnostics: {e}")

            # Always use the seller_product_url from the lowest-priced offer
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
                _LOGGER.error("[html_extractor] No valid seller URL found in offers. Extraction failure.")

            url_candidates = find_url_candidates(product_data)
            _LOGGER.info(f"[DIAG][html_extractor] All URL candidates in product_data: {url_candidates}")

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
        _LOGGER.error(f"BuyWisely HtmlExtractor: Error parsing hydration data: {e}")
    return raw_data