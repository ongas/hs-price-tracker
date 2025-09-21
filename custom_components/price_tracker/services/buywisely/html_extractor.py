import logging
import re
from custom_components.price_tracker.services.buywisely.buywisely_hydration_parser import extract_and_parse_all_hydration_data as parse_nextjs_hydration_data
from custom_components.price_tracker.services.buywisely.json_parser_utils import is_valid_seller_url

_LOGGER = logging.getLogger(__name__)



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

    parsed_data_list = parser_func(html)

    product_data = None
    if parsed_data_list:
        # The parse_nextjs_hydration_data function already extracts the product data,
        # so we can directly use the first item from the returned list.
        product_data = parsed_data_list[0]

    _LOGGER.debug(f"[DIAG][html_extractor] parsed_data_list after initial parsing: {parsed_data_list}")
    _LOGGER.debug(f"[DIAG][html_extractor] product_data after all searches: {product_data}")

    if product_data:
        _LOGGER.debug(f"[DIAG][html_extractor] Extracted title: {product_data.get('title')}")
        _LOGGER.debug(f"[DIAG][html_extractor] Extracted image: {product_data.get('image')}")
        _LOGGER.debug(f"[DIAG][html_extractor] Extracted offers: {product_data.get('offers')}")
        title = product_data.get('title')
        brand = title.split(' ')[0] if title else ''
        offers = product_data.get('offers', [])
        offers = offers[:10]
        # Deep diagnostics: log the full offers list and all candidate seller_product_url values
        try:
            all_seller_urls = [offer.get('seller_product_url') for offer in offers if 'seller_product_url' in offer]
            _LOGGER.debug(f"[DIAG][html_extractor] Full offers list: {offers}")
            _LOGGER.debug(f"[DIAG][html_extractor] All candidate seller_product_url values: {all_seller_urls}")
        except Exception as e:
            _LOGGER.error(f"[DIAG][html_extractor] Exception logging offers diagnostics: {e}")

        # Always use the seller_product_url from the lowest-priced offer


        lowest_offer = None
        lowest_price = None
        main_url = ""
        _LOGGER.debug(f"[DIAG][html_extractor] Starting lowest price calculation. Offers count: {len(offers)}")
        for offer in offers:
            price = offer.get('base_price')
            _LOGGER.debug(f"[DIAG][html_extractor] Processing offer: {offer.get('seller_product_url')}, base_price: {price}")
            if price is not None:
                try:
                    price_val = float(price)
                    _LOGGER.debug(f"[DIAG][html_extractor] Converted price_val: {price_val}")
                    if lowest_price is None or price_val < lowest_price:
                        lowest_price = price_val
                        lowest_offer = offer
                        _LOGGER.debug(f"[DIAG][html_extractor] New lowest_price: {lowest_price}")
                except Exception as e:
                    _LOGGER.warning(f"[DIAG][html_extractor] Could not convert offer price to float: {price}. Error: {e}")
                    continue
        _LOGGER.debug(f"[DIAG][html_extractor] Finished lowest price calculation. Lowest price found: {lowest_price}")
        _LOGGER.debug(f"[DIAG][html_extractor] Lowest offer: {lowest_offer}")
        if lowest_offer:
            seller_url_candidate = lowest_offer.get('seller_product_url')
            _LOGGER.debug(f"[DIAG][html_extractor] Seller URL candidate from lowest offer: {seller_url_candidate}")
            if is_valid_seller_url(seller_url_candidate):
                main_url = seller_url_candidate
                _LOGGER.debug(f"[DIAG][html_extractor] main_url set from seller_url_candidate: {main_url}")
            else:
                _LOGGER.debug(f"[DIAG][html_extractor] Seller URL candidate is not valid: {seller_url_candidate}")

        raw_data = {
            'title': title,
            'price': lowest_price, # This is the base price
            'image': product_data.get('image'),
            'currency': product_data.get('currency', 'AUD'),
            'availability': 'In Stock' if offers else 'Out of Stock',
            'brand': brand,
            'url': main_url,
            'offers': offers,
            'delivery_price': lowest_offer.get('shipping') if lowest_offer else None, # Add delivery price
        }
        _LOGGER.debug(f"[DIAG][html_extractor] raw_data after hydration extraction: {raw_data}")
        _LOGGER.debug(f"[DIAG][html_extractor] raw_data[\"url\"] set to: {main_url}")
        return raw_data
    else:
        _LOGGER.debug("BuyWisely HtmlExtractor: Product data not found in any supported hydration format. Trying BeautifulSoup fallback.")
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            raw_data = {}

            # Attempt to extract price from the h2 tag with the specific class
            price_elem = soup.find('h2', class_="MuiBox-root mui-8t0bjo")
            _LOGGER.debug(f"[DIAG][html_extractor] price_elem (BeautifulSoup): {price_elem}")
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                _LOGGER.debug(f"[DIAG][html_extractor] price_text (BeautifulSoup): {price_text}")
                # Extract prices using a more robust regex for ranges like "$391.00 - $499.00"
                # This regex looks for one or two currency-like numbers
                prices = re.findall(r'\$?([\d,]+\.?\d*)', price_text)
                _LOGGER.debug(f"[DIAG][html_extractor] Extracted prices (BeautifulSoup): {prices}")
                if prices:
                    try:
                        # Prioritize the first price found as the main price
                        raw_data['price'] = float(prices[0].replace(',', ''))
                        _LOGGER.debug(f"[DIAG][html_extractor] Successfully extracted price via BeautifulSoup: {raw_data['price']}")
                        if len(prices) > 1:
                            raw_data['highest_price'] = float(prices[1].replace(',', ''))
                            _LOGGER.debug(f"[DIAG][html_extractor] Successfully extracted highest_price via BeautifulSoup: {raw_data['highest_price']}")
                    except ValueError as ve:
                        _LOGGER.warning(f"Could not convert extracted price(s) to float: {prices}. Error: {ve}")

            # Attempt to extract currency (basic, can be improved if needed)
            # For now, assume AUD if price is found and no other currency is explicitly found
            if 'price' in raw_data and 'currency' not in raw_data:
                raw_data['currency'] = 'AUD'
                _LOGGER.debug(f"[DIAG][html_extractor] Set currency to AUD. raw_data: {raw_data}")
            elif 'price' not in raw_data:
                raw_data['currency'] = None # Set currency to None if no price is found
                _LOGGER.debug(f"[DIAG][html_extractor] Price not found, setting currency to None. raw_data: {raw_data}")

            # Attempt to extract delivery price
            delivery_elem = soup.find('p', class_="mui-wn7dhf")
            _LOGGER.debug(f"[DIAG][html_extractor] delivery_elem (BeautifulSoup): {delivery_elem}")
            if delivery_elem:
                delivery_text = delivery_elem.get_text(separator=" ", strip=True) # Use separator to handle comments
                _LOGGER.debug(f"[DIAG][html_extractor] delivery_text (BeautifulSoup): {delivery_text}")
                delivery_prices = re.findall(r'\$?([\d,]+\.?\d*)', delivery_text)
                _LOGGER.debug(f"[DIAG][html_extractor] Extracted delivery_prices (BeautifulSoup): {delivery_prices}")
                if delivery_prices:
                    try:
                        raw_data['delivery_price'] = float(delivery_prices[0].replace(',', ''))
                        _LOGGER.debug(f"[DIAG][html_extractor] Successfully extracted delivery_price via BeautifulSoup: {raw_data['delivery_price']}")
                    except ValueError as ve:
                        _LOGGER.warning(f"Could not convert extracted delivery price to float: {delivery_prices}. Error: {ve}")

            # Set availability based on price presence
            raw_data['availability'] = 'In Stock' if 'price' in raw_data else 'Out of Stock'

            _LOGGER.debug(f"BuyWisely HtmlExtractor: BeautifulSoup fallback extracted raw_data: {raw_data}")
            return raw_data
        except Exception as e:
            _LOGGER.error(f"BuyWisely HtmlExtractor: BeautifulSoup fallback failed: {e}")
            return {}
    _LOGGER.debug(f"[DIAG][html_extractor] Final product_data before return: {product_data}")
    return {} # Added this line to ensure a return in all cases