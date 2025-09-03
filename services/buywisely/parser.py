from bs4 import BeautifulSoup
import re
import logging
import bs4

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
        heading_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
        heading_prices = []
        # Extract prices from headings first
        for tag in heading_tags:
            for heading in soup.find_all(tag):
                heading_text = heading.get_text()
                # Support $ and €
                matches_dollar = re.findall(r'\$\s*([\d,]+\.?\d*)', heading_text)
                matches_euro = re.findall(r'€\s*([\d,]+\.?\d*)', heading_text)
                for match in matches_dollar:
                    try:
                        value = float(match.replace(',', ''))
                        heading_prices.append((value, heading_text, 'AUD'))
                    except Exception:
                        continue
                for match in matches_euro:
                    try:
                        value = float(match.replace(',', ''))
                        heading_prices.append((value, heading_text, 'EUR'))
                    except Exception:
                        continue
        # Log heading price candidates
        _LOGGER.debug(f"BuyWisely Parser: Heading price candidates: {heading_prices}")
        # If heading prices found, prefer the largest (most likely product price)
        if heading_prices:
            heading_prices_sorted = sorted(heading_prices, key=lambda x: x[0])
            price, source_text, currency = heading_prices_sorted[0]
            _LOGGER.debug(f"BuyWisely Parser: Selected heading price (lowest): {price} from text: {source_text}, currency: {currency}")
        else:
            # Fallback: Extract all prices from text, but ignore delivery/fee prices
            text = soup.get_text()
            price_matches_dollar = re.finditer(r'\$\s*([\d,]+\.?\d*)', text)
            price_matches_euro = re.finditer(r'€\s*([\d,]+\.?\d*)', text)
            for match in price_matches_dollar:
                value = None
                try:
                    value = float(match.group(1).replace(',', ''))
                except Exception:
                    continue
                after = text[match.end():match.end()+20].lower()
                if 'delivery' in after or 'fee' in after:
                    _LOGGER.debug(f"BuyWisely Parser: Ignoring price {value} due to context: {after}")
                    continue
                prices.append((value, text[max(0, match.start()-30):match.end()+30], 'AUD'))
            for match in price_matches_euro:
                value = None
                try:
                    value = float(match.group(1).replace(',', ''))
                except Exception:
                    continue
                after = text[match.end():match.end()+20].lower()
                if 'delivery' in after or 'fee' in after:
                    _LOGGER.debug(f"BuyWisely Parser: Ignoring euro price {value} due to context: {after}")
                    continue
                prices.append((value, text[max(0, match.start()-30):match.end()+30], 'EUR'))
            # Log all price candidates
            _LOGGER.debug(f"BuyWisely Parser: All price candidates: {prices}")
            # Prefer largest price (most likely product price)
            if prices:
                prices_sorted = sorted(prices, key=lambda x: x[0])
                price, source_text, currency = prices_sorted[0]
                _LOGGER.debug(f"BuyWisely Parser: Selected fallback price (lowest): {price} from context: {source_text}, currency: {currency}")
            else:
                price = None
        _LOGGER.debug(f"BuyWisely Parser: Final selected price: {price}, currency: {currency}")

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
            if generic_img and isinstance(generic_img, bs4.element.Tag):
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
        if meta_brand is not None and isinstance(meta_brand, bs4.element.Tag):
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

    # Extract vendor product detail URL from HTML (button or anchor)
    vendor_url = None
    # Look for anchor tags with href containing known vendor domains
    vendor_domains = [".com.au", ".com", ".net", ".org"]
    for a_tag in soup.find_all('a', href=True):
        if isinstance(a_tag, bs4.element.Tag):
            href = a_tag.get('href')
            if isinstance(href, str) and href.startswith("https://") and any(domain in href for domain in vendor_domains) and "buywisely.com.au" not in href:
                vendor_url = href
                _LOGGER.debug(f"BuyWisely Parser: Found vendor product URL: {vendor_url}")
                break
    # Fallback: if no vendor URL found, use BuyWisely product page
    if not vendor_url and product_id:
        vendor_url = f'https://www.buywisely.com.au/product/{product_id}'
    _LOGGER.debug(f"BuyWisely Parser: Final vendor URL: {vendor_url}")
    product_link = f'https://www.buywisely.com.au/product/{product_id}' if product_id else None
    _LOGGER.debug(f"BuyWisely Parser: Product link: {product_link}")
    _LOGGER.debug('[DIAG][parse_product] product_id=%s, price=%s, currency=%s, brand=%s, vendor_url=%s, link=%s', product_id, price, currency, brand, vendor_url, product_link)

    return {
        'title': title,
        'price': price,
        'image': image,
        'currency': currency,
        'availability': availability,
        'brand': brand,
        'url': vendor_url,
        'product_link': product_link
    }