import logging
import re
from custom_components.price_tracker.utilities.hydration_parser import parse_nextjs_hydration_data

_LOGGER = logging.getLogger(__name__)

def _find_product_data_recursive(data):
    if isinstance(data, dict):
        if 'offers' in data and isinstance(data['offers'], list):
            return data
        for key, value in data.items():
            result = _find_product_data_recursive(value)
            if result:
                return result
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, list):
                for sub_item in item:
                    result = _find_product_data_recursive(sub_item)
                    if result:
                        return result
            else:
                result = _find_product_data_recursive(item)
                if result:
                    return result
    return None

def find_product_with_offers(data):
    _LOGGER.debug(f"[DIAG][find_product_with_offers] Searching data: {data}")
    """Recursively search for a dict with an 'offers' key containing a list of dicts with 'seller_product_url'."""
    if isinstance(data, dict):
        if 'offers' in data and isinstance(data['offers'], list) and any(isinstance(o, dict) and 'seller_product_url' in o for o in data['offers']):
            _LOGGER.debug(f"[DIAG][find_product_with_offers] Found product with offers: {data}")
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
    _LOGGER.debug(f"[DIAG][find_product_with_offers] No product with offers found in: {data}")
    return None

def extract_product_data_from_html(html: str, parser_func=None) -> dict:
    """Extracts product data from BuyWisely HTML content."""
    _LOGGER.info("BuyWisely HtmlExtractor: Starting HTML extraction")
    if parser_func is None:
        parser_func = parse_nextjs_hydration_data

    parsed_data = parser_func(html)

    product_data = None
    if isinstance(parsed_data, list):
        for item in parsed_data:
            if isinstance(item, list) and len(item) > 1 and isinstance(item[1], list):
                for extracted_item in item[1]:
                    if isinstance(extracted_item, list) and len(extracted_item) > 1:
                        # The actual data is in extracted_item[1] or extracted_item[2]
                        # depending on whether it's [type, data] or [type, id, data]
                        data_candidate = None
                        if len(extracted_item) == 2 and isinstance(extracted_item[1], dict):
                            data_candidate = extracted_item[1]
                        elif len(extracted_item) == 3 and isinstance(extracted_item[2], dict):
                            data_candidate = extracted_item[2]

                        if data_candidate:
                            found_recursive = _find_product_data_recursive(data_candidate)
                            if found_recursive:
                                product_data = found_recursive
                                break
                if product_data:
                    break
    elif isinstance(parsed_data, dict):
        # Original __NEXT_DATA__ format
        product_data = _find_product_data_recursive(parsed_data)

    # If not found or doesn't have offers, search recursively for offers
    if not (product_data and isinstance(product_data, dict) and 'offers' in product_data and isinstance(product_data['offers'], list) and product_data['offers']):
        if isinstance(parsed_data, list):
            for item in parsed_data:
                if isinstance(item, dict) and 'extracted_data' in item:
                    for extracted_item in item['extracted_data']:
                        if isinstance(extracted_item, dict) and 'data' in extracted_item:
                            found_recursive = find_product_with_offers(extracted_item['data'])
                            if found_recursive:
                                product_data = found_recursive
                                break
                    if product_data:
                        break
        else:
            product_data = find_product_with_offers(parsed_data)

    # Fallback to original recursive search if still not found
    if not product_data:
        if isinstance(parsed_data, list):
            for item in parsed_data:
                found_recursive = _find_product_data_recursive(item)
                if found_recursive:
                    product_data = found_recursive
                    break
            else:
                product_data = _find_product_data_recursive(parsed_data)

    _LOGGER.info(f"[DIAG] product_data after all searches: {product_data}")

    if product_data:
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
        main_url = ""
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
        if lowest_offer and is_valid_seller_url(lowest_offer.get('seller_product_url')):
            main_url = lowest_offer['seller_product_url']

        raw_data = {
            'title': title,
            'price': lowest_price,
            'image': product_data.get('image'),
            'currency': product_data.get('currency', 'AUD'),
            'availability': 'In Stock' if offers else 'Out of Stock',
            'brand': brand,
            'url': main_url,
            'offers': offers,
        }
        _LOGGER.info(f"[DIAG][html_extractor] raw_data[\"url\"] set to: {main_url}")
        return raw_data
    else:
        _LOGGER.info("BuyWisely HtmlExtractor: Product data not found in any supported hydration format. Trying BeautifulSoup fallback.")
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            raw_data = {}

            # Attempt to extract price
            price_elem = soup.find(class_="price")
            _LOGGER.debug(f"[DIAG][html_extractor] price_elem: {price_elem}")
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                _LOGGER.debug(f"[DIAG][html_extractor] price_text: {price_text}")
                # Clean price_text by removing non-numeric characters except for the dot
                cleaned_price_text = re.sub(r'[^0-9.]', '', price_text)
                _LOGGER.debug(f"[DIAG][html_extractor] cleaned_price_text: {cleaned_price_text}")
                match = re.search(r'\d+\.?\d*', cleaned_price_text)
                _LOGGER.debug(f"[DIAG][html_extractor] match: {match}")
                if match:
                    try:
                        raw_data['price'] = float(match.group(0))
                    except ValueError:
                        _LOGGER.warning(f"Could not convert extracted price to float: {match.group(0)}")

            # Attempt to extract currency (basic, can be improved if needed)
            # For now, assume AUD if price is found and no other currency is explicitly found
            if 'price' in raw_data and 'currency' not in raw_data:
                raw_data['currency'] = 'AUD'
            elif 'price' not in raw_data:
                raw_data['currency'] = None # Set currency to None if no price is found

            # Set availability based on price presence
            raw_data['availability'] = 'In Stock' if 'price' in raw_data else 'Out of Stock'

            _LOGGER.info(f"BuyWisely HtmlExtractor: BeautifulSoup fallback extracted raw_data: {raw_data}")
            return raw_data
        except Exception as e:
            _LOGGER.error(f"BuyWisely HtmlExtractor: BeautifulSoup fallback failed: {e}")
            return {}
    return {} # Added this line to ensure a return in all cases