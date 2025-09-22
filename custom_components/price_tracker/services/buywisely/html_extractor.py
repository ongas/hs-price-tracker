import logging
import re
import json
from .hydration_parser import extract_and_parse_all_hydration_data
from bs4 import BeautifulSoup

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
    parsed_data = []
    try:
        parsed_data = extract_and_parse_all_hydration_data(html)
        # Deep diagnostics: log the entire parsed_data (hydration data)
        try:
            import json as _json
            _LOGGER.info(f"[DIAG][html_extractor] Full parsed_data (hydration): { _json.dumps(parsed_data, default=str)[:10000] }")
        except Exception as e:
            _LOGGER.error(f"[DIAG][html_extractor] Exception logging full parsed_data: {e}")
        _LOGGER.info(f"[DIAG] Parsed data from hydration_parser: {parsed_data}")
    except Exception as e:
        _LOGGER.error(f"BuyWisely HtmlExtractor: Error parsing with hydration_parser: {e}")
        parsed_data = []

    # If parsed_data is empty or not as expected, fallback to manual extraction
    if not parsed_data or (isinstance(parsed_data, list) and not parsed_data):
        _LOGGER.warning("[DIAG] HydrationDataExtractor returned empty, attempting manual __NEXT_DATA__ extraction.")
        match = re.search(r'<script[^>]*id=["\"]__NEXT_DATA__["\"][^>]*>(.*?)</script>', html, re.DOTALL)
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
    if parsed_data: # Changed from 'if product_data:' to 'if parsed_data:'
        product_data = _find_product_data_recursive(parsed_data) # Find product data from the parsed_data
    
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
            if re.search(r"\\.(jpg|jpeg|png|gif|webp|svg|bmp|tiff)(\\?|$)", url, re.IGNORECASE):
                return False
            if product_data and url == product_data.get('image'):
                return False
            if re.search(r"buywisely\\.com\\.au", url, re.IGNORECASE):
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


        # find_url_candidates is not defined; skipping this diagnostic for now

        # Always set 'title' in raw_data if present in product_data, even if offers is empty or missing

        raw_data = {
            'title': title if title else None,
            'price': product_data.get('lowest_price'),
            'image': product_data.get('image'),
            'currency': product_data.get('currency', 'AUD'),
            'availability': 'In Stock' if offers else 'Out of Stock',
            'brand': brand,
            'url': main_url,
            'offers': offers,
        }
        _LOGGER.info(f"[DIAG][html_extractor] raw_data['url'] set to: {main_url}")


        # Always set 'title' in raw_data if present in product_data, even if offers is empty or missing
        raw_data = {
            'title': title if title else None,
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
            # from bs4 import BeautifulSoup # Already imported at the top
            soup = BeautifulSoup(html, 'html.parser')
            price_val = None
            currency_val = 'AUD'
            price_text = None
            title_val = None
            # Try to extract title from <title> or <h1> if present
            title_elem = soup.find('title')
            if title_elem and title_elem.get_text(strip=True):
                title_val = title_elem.get_text(strip=True)
            else:
                h1_elem = soup.find('h1')
                if h1_elem and h1_elem.get_text(strip=True):
                    title_val = h1_elem.get_text(strip=True)
            # Try .price class first
            price_elem = soup.find(class_="price")
            if price_elem:
                price_text = price_elem.get_text(strip=True)
            # If not found, try any element with $ or currency symbol
            if not price_text:
                # Look for any text with a currency symbol
                text_candidates = soup.find_all(string=True)
                for t in text_candidates:
                    if re.search(r'\$|AUD|EUR|₩|¥|원|円', t):
                        price_text = t.strip()
                        break
            # Extract price and currency
            if price_text:
                # Try to extract currency (always prefer explicit currency, fallback to AUD if $)
                currency_match = re.search(r'(AUD|EUR|₩|¥|원|円|USD|NZD|GBP|\$)', price_text)
                if currency_match:
                    if currency_match.group(1) == '$':
                        currency_val = 'AUD'
                    else:
                        currency_val = currency_match.group(1)
                # Extract price number (allow comma, dot)
                price_match = re.search(r'([\d,.]+)', price_text.replace(",", ""))
                if price_match:
                    try:
                        price_val = float(price_match.group(1))
                    except Exception:
                        price_val = None
            raw_data = {}
            if price_val is not None:
                raw_data['price'] = price_val
                raw_data['currency'] = currency_val
                raw_data['availability'] = 'In Stock'
                raw_data['brand'] = ''
                raw_data['offers'] = []
                if title_val:
                    raw_data['title'] = title_val
            else:
                raw_data['availability'] = 'Out of Stock'
                if title_val:
                    raw_data['title'] = title_val
            _LOGGER.info(f"BuyWisely HtmlExtractor: BeautifulSoup fallback extracted price: {price_val}, currency: {currency_val}, title: {title_val}")
        except Exception as e:
            _LOGGER.error(f"BuyWisely HtmlExtractor: BeautifulSoup fallback failed: {e}")
    return raw_data
