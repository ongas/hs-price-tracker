from bs4 import BeautifulSoup
import re
import logging
import bs4

_LOGGER = logging.getLogger(__name__)

def parse_product(html: str, crawl4ai_data: dict | None = None, product_id: str | None = None, recency_days: int = 7) -> dict:
    _LOGGER.debug(f"BuyWisely Parser: HTML content: {html[:500]}")
    soup = BeautifulSoup(html, 'html.parser')

    title_selector = 'h1'
    image_selector = 'div.MuiBox-root.mui-1ub93rr img'

    title_element = soup.select_one(title_selector)
    title = title_element.text.strip() if title_element else None
    _LOGGER.debug(f"BuyWisely Parser: Title: {title}")

    price = None
    currency = 'AUD' # Default currency
    product_data = {}
    image = None
    vendor_url = None

    # Extract price from the main product information section
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

    # Find all product containers
    product_containers = soup.select('.MuiGrid-item:has(.MuiBox-root.mui-1ebnygn)')[:10]
    _LOGGER.debug(f"BuyWisely Parser: Found {len(product_containers)} product containers.")

    if product_containers:
        # Get the first product container, which should be the lowest price
        first_product = product_containers[0]
        _LOGGER.debug(f"BuyWisely Parser: First product container HTML: {first_product.prettify()}")

        # Extract vendor URL from the first product container
        vendor_link = first_product.find('a', string=re.compile("Go to store", re.IGNORECASE))
        if vendor_link and vendor_link.has_attr('href'):
            vendor_url = vendor_link['href']
            if vendor_url.startswith('/'):
                vendor_url = f"https://buywisely.com.au{vendor_url}"
            _LOGGER.debug(f"BuyWisely Parser: Found vendor product URL: {vendor_url}")

    # Fallback for image
    if image is None:
        image_element = soup.select_one(image_selector)
        if image_element and 'src' in image_element.attrs:
            image = image_element['src']
            if image and isinstance(image, str) and image.startswith('/'):
                image = 'https://buywisely.com.au' + image
        # If still no image, try any <img> tag
        if image is None:
            generic_img = soup.find('img')
            if generic_img and isinstance(generic_img, bs4.element.Tag):
                image = generic_img.get('src')

    availability = 'In Stock' if price else 'Out of Stock'
    brand = None
    meta_brand = soup.find('meta', attrs={'name': 'brand'})
    if meta_brand is not None and isinstance(meta_brand, bs4.element.Tag):
        brand = meta_brand.get('content')
    if not brand and title:
        brand = title.split(' ')[0]

    product_link = f'https://www.buywisely.com.au/product/{product_id}' if product_id else None

    return {
        'title': title,
        'price': price,
        'image': image,
        'currency': currency,
        'availability': availability,
        'brand': brand,
        'url': vendor_url,
        'product_link': product_link,
        'product_data': product_data,
    }