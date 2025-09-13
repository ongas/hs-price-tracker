import logging
from nextjs_hydration_parser import NextJSHydrationDataExtractor

_LOGGER = logging.getLogger(__name__)

def extract_product_data_from_html(html: str) -> dict:
    """Extracts product data from BuyWisely HTML content."""
    _LOGGER.info("BuyWisely HtmlExtractor: Starting HTML extraction")
    extractor = NextJSHydrationDataExtractor()
    
    raw_data = {}
    
    try:
        parsed_data = extractor.parse(html)
        _LOGGER.info(f"BuyWisely HtmlExtractor: Parsed data from nextjs_hydration_parser: {parsed_data}")

        # The nextjs_hydration_parser returns a list of dictionaries.
        # We need to find the dictionary that contains the product data.
        for item in parsed_data:
            if isinstance(item, dict) and 'props' in item and 'pageProps' in item['props'] and 'product' in item['props']['pageProps']:
                product_data = item['props']['pageProps']['product']
                break

        if product_data:
            _LOGGER.info(f"BuyWisely HtmlExtractor: Found product data: {product_data}")
            title = product_data.get('title')
            slug = product_data.get('slug')
            
            vendor_url = None
            if slug:
                vendor_url = f'https://www.buywisely.com.au/product/{slug}'
                _LOGGER.info(f"BuyWisely HtmlExtractor: Constructed vendor_url: {vendor_url}")
            else:
                _LOGGER.info("BuyWisely HtmlExtractor: Slug not found in product data.")

            brand = title.split(' ')[0] if title else ''
            
            offers = product_data.get('offers', [])
            offers = offers[:10]
            _LOGGER.info(f"BuyWisely HtmlExtractor: Extracted {len(offers)} offers")

            raw_data = {
                'title': title,
                'price': product_data.get('lowest_price'),
                'image': product_data.get('image'),
                'currency': 'AUD',  # Assuming AUD for BuyWisely
                'availability': 'In Stock' if offers else 'Out of Stock',
                'brand': brand,
                'url': vendor_url,
                'offers': offers,
            }
        else:
            _LOGGER.info("BuyWisely HtmlExtractor: Product data not found in __NEXT_DATA__.")

    except Exception as e:
        _LOGGER.error(f"BuyWisely HtmlExtractor: Error parsing with nextjs_hydration_parser: {e}")

    return raw_data