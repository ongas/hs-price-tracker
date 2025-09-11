import re
import logging
from nextjs_hydration_parser import NextJSHydrationDataExtractor
from .html_utils import extract_image, extract_title


_LOGGER = logging.getLogger(__name__)


def _find_nested_product_data(data):
    """Recursively searches for the product data in the dictionary or list."""
    if isinstance(data, dict):
        if 'product' in data:
            return data['product']
        for key, value in data.items():
            result = _find_nested_product_data(value)
            if result:
                return result
    elif isinstance(data, list):
        for item in data:
            result = _find_nested_product_data(item)
            if result:
                return result
    return None

def parse_product(html: str, product_id: str | None = None, recency_days: int = 7) -> dict:
    extractor = NextJSHydrationDataExtractor()
    _LOGGER.debug(f"BuyWisely Parser: HTML content: {html[:500]}")
    title = None
    price = None
    currency = 'AUD'
    image = None
    vendor_url = None
    brand = ""
    product_link = None
    availability = 'Out of Stock'
    offers = []
    
    try:
        parsed_data = extractor.parse(html)
        _LOGGER.debug(f"BuyWisely Parser: Parsed data from nextjs_hydration_parser: {parsed_data}")

        # Try to find product_data and offers within the parsed_data
        found_product_data = _find_nested_product_data(parsed_data)

        if found_product_data:
            title = found_product_data.get('title')
            slug = found_product_data.get('slug')
            if slug:
                product_link = f'https://www.buywisely.com.au/product/{slug}'
                vendor_url = product_link
            if title:
                brand = title.split(' ')[0]
            
            # Extract offers directly from found_product_data
            offers = found_product_data.get('offers', [])
            _LOGGER.debug(f"BuyWisely Parser: Offers extracted from product_data: {offers}")

            if offers:
                # Find the lowest price from the offers
                def get_base_price(offer):
                    try:
                        return float(offer.get('base_price', float('inf')))
                    except ValueError:
                        return float('inf')
                
                lowest_offer = min(offers, key=get_base_price)
                price = lowest_offer.get('base_price')
                currency = 'AUD' # Assuming AUD for BuyWisely
                availability = 'In Stock' if price is not None else 'Out of Stock'
        
    except Exception as e:
        _LOGGER.error(f"BuyWisely Parser: Error parsing with nextjs_hydration_parser: {e}")

    # Fallbacks using HTML (only if primary extraction failed for title/price)
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    if not title:
        title = extract_title(soup)
    if not price:
        all_h3_elements = soup.select('h3')
        extracted_prices = []
        for h3_element in all_h3_elements[:10]:
            price_text = h3_element.get_text()
            matches = re.findall(r'([\$€])\s*([\d,]+\.?\d*)', price_text)
            if matches:
                for symbol, value in matches:
                    try:
                        extracted_prices.append((float(value.replace(',', '')), symbol))
                    except ValueError:
                        pass
            if extracted_prices:
                min_price_tuple = min(extracted_prices, key=lambda x: x[0])
                price = min_price_tuple[0]
                symbol = min_price_tuple[1]
                if symbol == '$':
                    currency = 'AUD'
                elif symbol == '€':
                    currency = 'EUR'
                else:
                    currency = 'AUD'
                _LOGGER.debug(f"BuyWisely Parser: Selected minimum price from H3: {price}, Currency: {currency}")

    if price and not availability: # Set availability if price found by fallback
        availability = 'In Stock'

    if not image:
        image = extract_image(soup)
    if not brand and title:
        brand = title.split(' ')[0] if title else None

    # Ensure offers are always sliced to 10 if they exist
    if offers:
        offers = offers[:10]
    _LOGGER.debug(f"BuyWisely Parser: Final offers after slicing: {offers}")

    return {
        'title': title,
        'price': price,
        'image': image,
        'currency': currency,
        'availability': availability,
        'brand': brand,
        'url': vendor_url,
        'product_link': product_link,
        'offers': offers,
    }