from bs4 import BeautifulSoup
import re
import logging
import bs4
import json
from nextjs_hydration_parser import NextJSHydrationDataExtractor

_LOGGER = logging.getLogger(__name__)

def find_product_data(data):
    """Recursively searches for the product data in the dictionary."""
    if isinstance(data, dict):
        if 'title' in data and 'slug' in data:
            return data
        for key, value in data.items():
            result = find_product_data(value)
            if result:
                return result
    elif isinstance(data, list):
        for item in data:
            result = find_product_data(item)
            if result:
                return result
    return None

def parse_product(html: str, crawl4ai_data: dict | None = None, product_id: str | None = None, recency_days: int = 7) -> dict:
    extractor = NextJSHydrationDataExtractor()
    _LOGGER.debug(f"BuyWisely Parser: HTML content: {html[:500]}")
    
    title = None
    price = None
    currency = 'AUD' # Default currency
    image = None
    vendor_url = None
    brand = "" # Initialize brand with an empty string
    product_link = None
    availability = 'Out of Stock'

    try:
        parsed_data = extractor.parse(html)
        _LOGGER.debug(f"BuyWisely Parser: Parsed data from nextjs_hydration_parser: {parsed_data}")

        product_data = find_product_data(parsed_data)

        if product_data:
            title = product_data.get('title')
            slug = product_data.get('slug')
            if slug:
                product_link = f'https://www.buywisely.com.au/product/{slug}'
                vendor_url = product_link # As per problem summary, vendor_url is the product page on buywisely
            
            if title:
                brand = title.split(' ')[0]

    except Exception as e:
        _LOGGER.error(f"BuyWisely Parser: Error parsing with nextjs_hydration_parser: {e}")

    # Keep the existing logic for price and image as a fallback
    soup = BeautifulSoup(html, 'html.parser')
    if not title:
        title_element = soup.select_one('h1')
        title = title_element.text.strip() if title_element else None

    if not price:
        price_range_element = soup.select_one('.MuiBox-root.mui-1lekzkb h2')
        if price_range_element:
            price_text = price_range_element.get_text()
            matches = re.findall(r'\$\s*([\d,]+\.?\d*)', price_text)
            if matches:
                try:
                    price = float(matches[0].replace(',', ''))
                    _LOGGER.debug(f"BuyWisely Parser: Selected price from main section: {price}")
                except ValueError:
                    price = None
    
    if price:
        availability = 'In Stock'

    if not image:
        image_element = soup.select_one('div.MuiBox-root.mui-1ub93rr img')
        if image_element and 'src' in image_element.attrs:
            image = image_element['src']
            if image and isinstance(image, str) and image.startswith('/'):
                image = 'https://buywisely.com.au' + image
        if image is None:
            generic_img = soup.find('img')
            if generic_img and isinstance(generic_img, bs4.element.Tag):
                image = generic_img.get('src')

    if not brand and title:
        brand = title.split(' ')[0]

    return {
        'title': title,
        'price': price,
        'image': image,
        'currency': currency,
        'availability': availability,
        'brand': brand,
        'url': vendor_url,
        'product_link': product_link,
    }
