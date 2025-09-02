from bs4 import BeautifulSoup
import re
import logging

_LOGGER = logging.getLogger(__name__)

def parse_product(html: str, crawl4ai_data: dict | None = None, product_id: str | None = None) -> dict:
    # ...existing code...
    soup = BeautifulSoup(html, 'html.parser')

    
    image_selector = 'div.MuiBox-root.mui-1ub93rr img'

    title = soup.title.string.strip() if soup.title and soup.title.string else None
    _LOGGER.debug(f"BuyWisely Parser: Title: {title}")

    price = None
    currency = 'AUD' # Default currency
    
    # Try to get price from crawl4ai data first, using product_id if provided
    if crawl4ai_data and 'products' in crawl4ai_data and crawl4ai_data['products']:
        product_data = None
        if product_id:
            for prod in crawl4ai_data['products']:
                if str(prod.get('id')) == str(product_id):
                    product_data = prod
                    break
        if not product_data:
            product_data = crawl4ai_data['products'][0]
        if 'product_status' in product_data and 'lowest_price' in product_data['product_status']:
            price = float(product_data['product_status']['lowest_price'])
            _LOGGER.debug(f"BuyWisely Parser: Price from crawl4ai: {price}")
            # Assuming currency is AUD for buywisely.com.au, or can be extracted if available in crawl4ai data

    # Fallback to BeautifulSoup if crawl4ai data doesn't provide the price
    if price is None:
        price_element = soup.select_one('h3')
        if price_element:
            price_text = price_element.text.strip()
            _LOGGER.debug(f"BuyWisely Parser: Price element text: '{price_text}'")
            price_match = re.search(r'\$\s*([\d,]+\.?\d*)', price_text)
            if price_match:
                _LOGGER.debug(f"BuyWisely Parser: Regex matched: {price_match.group(0)}")
                _LOGGER.debug(f"BuyWisely Parser: Captured group 1: {price_match.group(1)}")
                try:
                    price = float(price_match.group(1).replace(',', ''))
                    _LOGGER.debug(f"BuyWisely Parser: Final price from targeted element: {price}")
                except (ValueError, TypeError) as e:
                    _LOGGER.error(f"BuyWisely Parser: Error converting price: {e}")
            else:
                _LOGGER.debug("BuyWisely Parser: No price found with targeted regex in element.")
        else:
            _LOGGER.debug("BuyWisely Parser: No price element found with selector h3.")

    image = None
    # Try to get image from crawl4ai data first
    if crawl4ai_data and 'products' in crawl4ai_data and crawl4ai_data['products']:
        product_data = None
        if product_id:
            for prod in crawl4ai_data['products']:
                if str(prod.get('id')) == str(product_id):
                    product_data = prod
                    break
        if not product_data:
            product_data = crawl4ai_data['products'][0]
        if 'media' in product_data and 'images' in product_data['media'] and product_data['media']['images']:
            image = product_data['media']['images'][0] # Taking the first image for now
            _LOGGER.debug(f"BuyWisely Parser: Image from crawl4ai: {image}")

    # Fallback to BeautifulSoup if crawl4ai data doesn't provide the image
    if image is None:
        image_element = soup.select_one(image_selector)
        if image_element and 'src' in image_element.attrs:
            image = image_element['src']
            if image and isinstance(image, str) and image.startswith('/'):
                image = 'https://buywisely.com.au' + image
        # If still no image, try any <img> tag
        if image is None:
            generic_img = soup.find('img')
            from bs4 import Tag
            if generic_img and isinstance(generic_img, Tag):
                image = generic_img.get('src')
    
    _LOGGER.debug(f"BuyWisely Parser: Final image: {image}")
    availability = 'In Stock' if price else 'Out of Stock'
    _LOGGER.debug(f"BuyWisely Parser: Availability: {availability}")

    # Extract brand/vendor from crawl4ai_data if available
    brand = None
    if crawl4ai_data and 'products' in crawl4ai_data and crawl4ai_data['products']:
        product_data = None
        if product_id:
            for prod in crawl4ai_data['products']:
                if str(prod.get('id')) == str(product_id):
                    product_data = prod
                    break
        if not product_data:
            product_data = crawl4ai_data['products'][0]
        brand = product_data.get('brand') or product_data.get('vendor') or None
        _LOGGER.debug(f"BuyWisely Parser: Brand/Vendor from crawl4ai: {brand}")
    # Fallback: try to extract brand from HTML meta or text
    if brand is None:
        meta_brand = soup.find('meta', attrs={'name': 'brand'})
        from bs4 import Tag
        if meta_brand is not None and isinstance(meta_brand, Tag):
            brand = meta_brand.get('content')
        # Try regex for 'Brand:' in text
        brand_match = re.search(r'Brand:\s*([\w\s]+)', soup.get_text())
        if brand_match:
            brand = brand_match.group(1).strip()
        # Fallback: Try to extract from the title if a specific brand element is not found
        if brand is None and title:
            # Assuming brand is the first word of the title
            brand_from_title = title.split(' ')[0]
            if brand_from_title and brand_from_title[0].isupper():
                brand = brand_from_title
            _LOGGER.debug(f"BuyWisely Parser: Brand from title fallback: {brand}")
        _LOGGER.debug(f"BuyWisely Parser: Brand/Vendor from HTML: {brand}")

    # Product link
    product_link = None
    if product_id:
        product_link = f'https://www.buywisely.com.au/product/{product_id}'
    else:
        product_link = None
    _LOGGER.debug(f"BuyWisely Parser: Product link: {product_link}")

    

    return {
        'title': title,
        'price': price,
        'image': image,
        'currency': currency,
        'availability': availability,
        'brand': brand,
        'product_link': product_link
    }