import logging
import re
import json
from typing import Optional
from bs4 import BeautifulSoup
from .nextjs_hydration_parser import NextJSHydrationDataExtractor

_LOGGER = logging.getLogger(__name__)


def _find_product_data_recursive(data):
    """Recursively finds product data within a nested dictionary or list.
    Recognizes dicts with 'title' and 'offers' keys as product data, not just under 'product'."""
    if isinstance(data, dict):
        # Recognize a product dict by the presence of 'title' and 'offers' keys
        if (
            'title' in data and 'offers' in data and isinstance(data['offers'], list)
        ):
            return data
        # Legacy: dict with 'product' key
        if 'product' in data and isinstance(data['product'], dict):
            return data['product']
        for value in data.values():
            result = _find_product_data_recursive(value)
            if result:
                return result
    elif isinstance(data, list):
        for item in data:
            result = _find_product_data_recursive(item)
            if result:
                return result
    return None


def _extract_hydration_data(html: str) -> dict:
    """Extracts and parses __NEXT_DATA__ from HTML, with manual fallback."""
    extractor = NextJSHydrationDataExtractor()
    parsed_data = extractor.parse(html)

    _LOGGER.info(
        f"[DIAG] Full parsed_data (hydration): "
        f"{json.dumps(parsed_data, default=str)[:10000]}"
    )
    _LOGGER.info(f"[DIAG] Parsed data from nextjs_hydration_parser: {parsed_data}")

    if not parsed_data or (isinstance(parsed_data, list) and not parsed_data):
        _LOGGER.warning(
            "[DIAG] NextJSHydrationDataExtractor returned empty, "
            "attempting manual __NEXT_DATA__ extraction."
        )
        match = re.search(
            r'<script[^>]*id=["\\]?__NEXT_DATA__["\\]?[^>]*>(.*?)</script>',
            html, re.DOTALL
        )
        if match:
            next_data_json = match.group(1)
            try:
                parsed_data = json.loads(next_data_json)
                _LOGGER.info(
                    f"[DIAG] Manually extracted __NEXT_DATA__ JSON: "
                    f"{type(parsed_data)}"
                )
            except json.JSONDecodeError as e:
                _LOGGER.error(f"[DIAG] Failed to parse __NEXT_DATA__ JSON: {e}")
                parsed_data = {}
    return parsed_data


def _is_valid_seller_url(url: str, product_image_url: Optional[str]) -> bool:
    """Checks if a given URL is a valid seller product URL."""
    if not url or not isinstance(url, str):
        return False
    url = url.strip()
    if re.search(r"\.(jpg|jpeg|png|gif|webp|svg|bmp|tiff)(\?|$)", url,
                   re.IGNORECASE):
        return False
    if product_image_url and url == product_image_url:
        return False
    if re.search(r"buywisely\.com\.au", url, re.IGNORECASE):
        return False
    return url.startswith("http")


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
        _LOGGER.debug("[DIAG][_extract_from_beautifulsoup] Price is None, setting availability to Out of Stock.")
    _LOGGER.info(
        f"BuyWisely HtmlExtractor: BeautifulSoup fallback extracted "
        f"price: {price_val}, currency: {currency_val}, title: {title_val}"
    )
    return raw_data


def extract_product_data_from_html(html: str) -> dict:
    """Extracts product data from BuyWisely HTML content."""
    _LOGGER.info("BuyWisely HtmlExtractor: Starting HTML extraction")
    raw_data = {}
    try:
        parsed_data = _extract_hydration_data(html)
        product_data = _find_product_data_recursive(parsed_data)

        if product_data:
            offers, main_url = _process_product_offers(product_data)
            title = product_data.get('title')
            brand = title.split(' ')[0] if title else ''

            raw_data = {
                'title': title,
                'name': product_data.get('name') or title,
                'product': product_data.get('product') or title,
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
            _LOGGER.info(
                "BuyWisely HtmlExtractor: Product data not found in any "
                "supported hydration format. Trying BeautifulSoup fallback."
            )
            raw_data = extract_from_beautifulsoup(html)

    except Exception as e:
        _LOGGER.error(f"BuyWisely HtmlExtractor: Error parsing HTML: {e}")
    return raw_data
