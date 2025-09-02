from bs4 import BeautifulSoup
import re
import logging

_LOGGER = logging.getLogger(__name__)

def parse_product(html: str, crawl4ai_data: dict | None = None, product_id: str | None = None) -> dict:
    _LOGGER.debug(f"BuyWisely Parser: HTML content: {html[:500]}")
    soup = BeautifulSoup(html, 'html.parser')

    title_selector = 'h2'
    image_selector = 'div.MuiBox-root.mui-1ub93rr img'

    title_element = soup.select_one(title_selector)
    title = title_element.text.strip() if title_element else None
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
        prices = []
        text = soup.get_text()
        _LOGGER.debug(f"BuyWisely Parser: Text for regex: {text[:500]}")
        price_matches = re.findall(r'\$\s*([\d,]+\.?\d*)', text)
        _LOGGER.debug(f"BuyWisely Parser: Regex matches: {price_matches}")
        for price_match in price_matches:
            try:
                price_value = float(price_match.replace(',', ''))
                prices.append(price_value)
            except (ValueError, TypeError):
                continue
        _LOGGER.debug(f"BuyWisely Parser: Found prices: {prices}")
        # Ignore zero values when selecting minimum price
        non_zero_prices = [p for p in prices if p > 0]
        price = min(non_zero_prices) if non_zero_prices else (min(prices) if prices else None)
        _LOGGER.debug(f"BuyWisely Parser: Final price after ignoring zeros: {price}")

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
            if generic_img and 'src' in generic_img.attrs:
                image = generic_img['src']
    
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
        if meta_brand is not None and hasattr(meta_brand, 'attrs') and 'content' in meta_brand.attrs:
            brand = meta_brand['content']
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

    # Guaranteed diagnostics: write extracted brand and product_link to /tmp/buywisely_parse_product.log
    try:
        with open('/tmp/buywisely_parse_product.log', 'a') as f:
            f.write(f"brand={brand}, product_link={product_link}, title={title}, price={price}, image={image}, currency={currency}, availability={availability}\n")
    except Exception:
        pass

    return {
        'title': title,
        'price': price,
        'image': image,
        'currency': currency,
        'availability': availability,
        'brand': brand,
        'product_link': product_link
    }