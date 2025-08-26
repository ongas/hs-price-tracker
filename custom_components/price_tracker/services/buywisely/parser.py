# Buywisely parser implementation
# TODO: Implement parse_product function here, matching other services

from bs4 import BeautifulSoup
import re

def parse_product(html: str, crawl4ai_data: dict | None = None, product_id: str | None = None) -> dict:
    soup = BeautifulSoup(html, 'html.parser')

    title_selector = 'h2'
    image_selector = 'div.MuiBox-root.mui-1ub93rr img'

    title_element = soup.select_one(title_selector)
    title = title_element.text.strip() if title_element else None

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
        # Assuming currency is AUD for buywisely.com.au, or can be extracted if available in crawl4ai data
        if 'media' in product_data and 'images' in product_data['media'] and product_data['media']['images']:
            image = product_data['media']['images'][0]
        else:
            image = None
    else:
        prices = []
        offer_cards = soup.select('div.MuiPaper-root.MuiCard-root.mui-raoxi0')
        for card in offer_cards:
            is_historical = card.select_one('p.MuiTypography-root.mui-1ik0owp')
            is_low_stock = card.select_one('p.MuiTypography-root.mui-4u7vn6')
            if not is_historical and not is_low_stock:
                price_element = card.select_one('h3.MuiBox-root.mui-mftzct')
                if price_element:
                    price_text = price_element.text.strip()
                    currency_match = re.search(r'([$€£¥])\s*([\d,]+\.?\d*)', price_text)
                    if currency_match:
                        currency_symbol = currency_match.group(1)
                        if currency_symbol == '$':
                            currency = 'AUD'
                        elif currency_symbol == '€':
                            currency = 'EUR'
                        elif currency_symbol == '£':
                            currency = 'GBP'
                        elif currency_symbol == '¥':
                            currency = 'JPY'
                        try:
                            price_value = float(currency_match.group(2).replace(',', ''))
                            prices.append(price_value)
                        except (ValueError, TypeError):
                            continue
        if not prices:
            h3_elements = soup.find_all('h3')
            for h3 in h3_elements:
                price_text = h3.text.strip()
                currency_match = re.search(r'([$€£¥])\s*([\d,]+\.?\d*)', price_text)
                if currency_match:
                    currency_symbol = currency_match.group(1)
                    if currency_symbol == '$':
                        currency = 'AUD'
                    elif currency_symbol == '€':
                        currency = 'EUR'
                    elif currency_symbol == '£':
                        currency = 'GBP'
                    elif currency_symbol == '¥':
                        currency = 'JPY'
                    try:
                        price_value = float(currency_match.group(2).replace(',', ''))
                        prices.append(price_value)
                    except (ValueError, TypeError):
                        continue
        price = min(prices) if prices else None
        image_element = soup.select_one(image_selector)
        image = image_element['src'] if image_element and 'src' in image_element.attrs else None
        if image and isinstance(image, str) and image.startswith('/'):
            image = 'https://buywisely.com.au' + image
        if image is None:
            generic_img = soup.find('img')
            if generic_img and hasattr(generic_img, 'get'):
                src = generic_img.get('src')
                if src:
                    image = src
    availability = 'In Stock' if price else 'Out of Stock'
    return {
        'title': title,
        'price': price,
        'image': image,
        'currency': currency,
        'availability': availability
    }
