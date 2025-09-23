import logging
import re
import json
from typing import Optional
from bs4 import BeautifulSoup
from .hydration_parser import extract_and_parse_all_hydration_data

_LOGGER = logging.getLogger(__name__)


def _find_product_data_recursive(data, path=""):
    _LOGGER.debug(f"[DIAG][_find_product_data_recursive] Processing data at path: {path}, type: {type(data)}")
    if isinstance(data, dict):
        # Check for the new product dict structure (title and offers)
        if 'title' in data and 'offers' in data and isinstance(data['offers'], list):
            _LOGGER.debug(f"[DIAG][_find_product_data_recursive] Found product data (title/offers) at path: {path}")
            return data
        # Legacy: dict with 'product' key
        if 'product' in data and isinstance(data['product'], dict):
            _LOGGER.debug(f"[DIAG][_find_product_data_recursive] Found product data (legacy 'product' key) at path: {path}")
            return data['product']
        for key, value in data.items():
            result = _find_product_data_recursive(value, f"{path}.{key}")
            if result:
                return result
    elif isinstance(data, list):
        _LOGGER.debug(f"[DIAG][_find_product_data_recursive] Iterating list of length {len(data)} at path: {path}")
        for i, item in enumerate(data):
            result = _find_product_data_recursive(item, f"{path}[{i}]")
            if result:
                return result
    return None


def _is_valid_seller_url(url: str, product_image_url: Optional[str]) -> bool:
    """Checks if a given URL is a valid seller product URL."""
    if not url or not isinstance(url, str):
        _LOGGER.debug(f"[DIAG][is_valid_seller_url] Invalid: URL is None or not a string. URL: {url}")
        return False
    url = url.strip()
    if re.search(r"\.(jpg|jpeg|png|gif|webp|svg|bmp|tiff)(\?|$)", url, re.IGNORECASE):
        _LOGGER.debug(f"[DIAG][is_valid_seller_url] Invalid: URL is an image URL. URL: {url}")
        return False
    if product_image_url and url == product_image_url:
        _LOGGER.debug(f"[DIAG][is_valid_seller_url] Invalid: URL matches product image URL. URL: {url}")
        return False
    if re.search(r"buywisely\.com\.au", url, re.IGNORECASE):
        _LOGGER.debug(f"[DIAG][is_valid_seller_url] Invalid: URL contains buywisely.com.au. URL: {url}")
        return False
    if not url.startswith("http"):
        _LOGGER.debug(f"[DIAG][is_valid_seller_url] Invalid: URL does not start with http. URL: {url}")
        return False
    _LOGGER.debug(f"[DIAG][is_valid_seller_url] Valid: URL passed all checks. URL: {url}")
    return True


def _process_product_offers(product_data: dict) -> tuple[list, str]:
    """Processes product offers to find the main URL and filter offers."""
    offers = product_data.get('offers', [])
    if not isinstance(offers, list):
        offers = []
    offers = offers[:10]  # Limit to first 10 offers

    all_seller_urls = [
        offer.get('seller_product_url') for offer in offers
        if isinstance(offer, dict) and 'seller_product_url' in offer
    ]
    _LOGGER.info(f"[DIAG][html_extractor] Full offers list: {offers}")
    _LOGGER.info(
        f"[DIAG][html_extractor] All candidate seller_product_url values: "
        f"{all_seller_urls}"
    )

    lowest_offer = None
    lowest_price = None
    for offer in offers:
        if not isinstance(offer, dict):
            continue
        price = offer.get('base_price')
        if price is None or price == '' or (isinstance(price, str) and not price.strip()):
            _LOGGER.warning(f"[DIAG] Offer has missing or empty base_price: {offer}")
            continue
        try:
            price_val = float(price)
            if lowest_price is None or price_val < lowest_price:
                lowest_price = price_val
                lowest_offer = offer
        except (ValueError, TypeError) as e:
            _LOGGER.warning(f"[DIAG] Could not parse price {price}: {e}")
            continue

    main_url = ""
    url_candidate = lowest_offer.get('seller_product_url') if lowest_offer else ''
    image_candidate = product_data.get('image') if product_data else ''
    if lowest_offer and _is_valid_seller_url(str(url_candidate or ''), image_candidate):
        main_url = str(url_candidate)
        _LOGGER.info(
            f"[DIAG][html_extractor] Extracted seller_product_url from "
            f"lowest-priced offer: {main_url}"
        )
    else:
        _LOGGER.error(
            "[html_extractor] No valid seller URL found in offers. "
            "Extraction failure."
        )
    return offers, main_url


def extract_from_beautifulsoup(html: str) -> dict:
    """Extracts product data using BeautifulSoup fallback."""
    soup = BeautifulSoup(html, 'html.parser')
    price_val = None
    currency_val = 'AUD'
    price_text = None
    title_val = None

    title_elem = soup.find('title')
    if title_elem and title_elem.get_text(strip=True):
        title_val = title_elem.get_text(strip=True)
    else:
        h1_elem = soup.find('h1')
        if h1_elem and h1_elem.get_text(strip=True):
            title_val = h1_elem.get_text(strip=True)

    price_elem = soup.find(class_="price")
    if price_elem:
        price_text = price_elem.get_text(strip=True)
    elif not price_text:
        for t in soup.find_all(string=True):
            if re.search(r'\$|AUD|EUR|₩|¥|원|円', t):
                price_text = t.strip()
                break

    if price_text:
        currency_match = re.search(r'(AUD|EUR|₩|¥|원|円|USD|NZD|GBP|\$)', price_text)
        if currency_match:
            if currency_match.group(1) == '$':
                currency_val = 'AUD'
            else:
                currency_val = currency_match.group(1)
        else:
            currency_val = 'AUD'

        price_match = re.search(r"([\d,.]+)", price_text.replace(",", ""))
        if price_match:
            try:
                price_val = float(price_match.group(1))
            except Exception:
                price_val = None
        else:
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
        _LOGGER.debug("[DIAG][_extract_from_beautifulsoup] Price is None, setting availability to Out of Stock.")
        if title_val:
            raw_data['title'] = title_val
    _LOGGER.info(
        f"BuyWisely HtmlExtractor: BeautifulSoup fallback extracted "
        f"price: {price_val}, currency: {currency_val}, title: {title_val}"
    )
    return raw_data


def extract_product_data_from_html(html: str) -> dict:
    """Extracts product data from BuyWisely HTML content."""
    raw_data = {}
    _LOGGER.info("BuyWisely HtmlExtractor: Starting HTML extraction")
    parsed_data_list = []
    try:
        parsed_data_list = extract_and_parse_all_hydration_data(html)
        _LOGGER.debug(f"[DIAG][html_extractor] Raw parsed_data_list from hydration_parser: {parsed_data_list}")
        try:
            import json as _json
            _LOGGER.info(f"[DIAG][html_extractor] Full parsed_data (hydration): { _json.dumps(parsed_data_list, default=str)[:10000] }")
        except Exception as e:
            _LOGGER.error(f"[DIAG][html_extractor] Exception logging full parsed_data: {e}")
        _LOGGER.info(f"[DIAG] Parsed data from hydration_parser: {parsed_data_list}")
    except Exception as e:
        _LOGGER.error(f"BuyWisely HtmlExtractor: Error parsing with hydration_parser: {e}")
        parsed_data_list = []

    if not parsed_data_list:
        _LOGGER.warning("[DIAG] HydrationDataExtractor returned empty, attempting manual __NEXT_DATA__ extraction.")
        match = re.search(r'<script[^>]*id=["__NEXT_DATA__"][^>]*>(.*?)</script>', html, re.DOTALL)
        if match:
            try:
                next_data_json = match.group(1)
                parsed_data_manual = json.loads(next_data_json)
                _LOGGER.info(f"[DIAG] Manually extracted __NEXT_DATA__ JSON: {type(parsed_data_manual)}")
                if isinstance(parsed_data_manual, list):
                    parsed_data_list.extend(parsed_data_manual)
                else:
                    parsed_data_list.append(parsed_data_manual)
            except Exception as e:
                _LOGGER.error(f"[DIAG] Failed to parse __NEXT_DATA__ JSON: {e}")
                parsed_data_list = []

    product_data = None
    for item in parsed_data_list:
        product_data = _find_product_data_recursive(item)
        if product_data:
            break
    _LOGGER.debug(f"[DIAG][html_extractor] Product data after recursive search: {product_data}")
    
    if product_data:
        _LOGGER.info(f"[DIAG][html_extractor] Found product data: {product_data}")
        title = product_data.get('title')
        brand = title.split(' ')[0] if title else ''
        offers, main_url = _process_product_offers(product_data)

        name_fields = ['title', 'name', 'product']
        name_value = None
        for field in name_fields:
            name_raw = product_data.get(field)
            if isinstance(name_raw, str) and name_raw.strip():
                name_value = name_raw.strip()
                _LOGGER.info(f"[DIAG][html_extractor] Product name found in field '{field}': {name_value}")
                break
        if not name_value:
            name_value = 'UNKNOWN'
            _LOGGER.warning(f"[DIAG][html_extractor] Product name not found in any of {name_fields}, defaulting to 'UNKNOWN'. product_data keys: {list(product_data.keys())}")


        raw_data = {
            'title': name_value,
            'price': product_data.get('lowest_price'),
            'image': product_data.get('image'),
            'currency': product_data.get('currency', 'AUD'),
            'availability': 'In Stock' if offers else 'Out of Stock',
            'brand': brand,
            'url': main_url,
            'offers': offers,
        }
        _LOGGER.info(f"[DIAG][html_extractor] raw_data before return: {raw_data}")
        return raw_data
    else:
        _LOGGER.info("BuyWisely HtmlExtractor: Product data not found in any supported hydration format. Trying BeautifulSoup fallback.")
        raw_data = extract_from_beautifulsoup(html)
        _LOGGER.debug(f"[DIAG][html_extractor] raw_data after BeautifulSoup fallback: {raw_data}")
    return raw_data