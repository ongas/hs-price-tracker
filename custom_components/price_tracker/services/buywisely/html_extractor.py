import logging
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
        parsed_data = extractor.parse(html)
        _LOGGER.info(f"BuyWisely HtmlExtractor: Parsed data from nextjs_hydration_parser: {parsed_data}")

        # Attempt to extract product data from the most common specific path
        try:
            if isinstance(parsed_data, list) and len(parsed_data) > 0 and \
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
            _LOGGER.info("BuyWisely HtmlExtractor: Product data not found in any supported hydration format.")
    except Exception as e:
        _LOGGER.error(f"BuyWisely HtmlExtractor: Error parsing with nextjs_hydration_parser: {e}")
    return raw_data