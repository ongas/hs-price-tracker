"""Data transformation for BuyWisely product data."""
import logging
import re
from typing import Optional
from bs4 import BeautifulSoup
from requests.exceptions import RequestException, Timeout

from custom_components.price_tracker.datas.item import ItemData, ItemStatus
from custom_components.price_tracker.datas.price import ItemPriceData
from custom_components.price_tracker.datas.category import ItemCategoryData
from custom_components.price_tracker.utilities.safe_request import SafeRequest, SafeRequestMethod
from custom_components.price_tracker.utilities.parser import parse_float

_LOGGER = logging.getLogger(__name__)

async def _fetch_and_parse_seller_price(url: str) -> Optional[float]:
    """
    Fetches the seller's product page and attempts to extract the price.
    Returns the extracted price as a float, or None if extraction fails.
    """
    request = SafeRequest()
    try:
        response = await request.request(method=SafeRequestMethod.GET, url=url)
        if not response.has:
            _LOGGER.error("Failed to fetch seller page for price validation: %s", url)
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # --- Start of new JSON parsing logic ---
        import json

        def _find_price_in_json(data):
            """Recursively search for a price in a JSON object."""
            if isinstance(data, dict):
                for key, value in data.items():
                    # Check if the key is a price-related term
                    if isinstance(key, str) and key.lower() in ['price', 'base_price', 'amount', 'priceamount']:
                        if isinstance(value, (int, float)):
                            return float(value)
                        if isinstance(value, str):
                            try:
                                return parse_float(value)
                            except (ValueError, TypeError):
                                pass  # Continue searching
                    
                    # Recurse into the value
                    found_price = _find_price_in_json(value)
                    if found_price is not None:
                        return found_price
            elif isinstance(data, list):
                for item in data:
                    found_price = _find_price_in_json(item)
                    if found_price is not None:
                        return found_price
            return None

        # 1. Prioritize searching for price in JSON within <script> tags
        for script_tag in soup.find_all('script'):
            try:
                # Look for Next.js data or other JSON data
                if script_tag.string and ('__NEXT_DATA__' in script_tag.string or 'application/json' in script_tag.get('type', '')):
                    json_data = json.loads(script_tag.string)
                    price = _find_price_in_json(json_data)
                    if price is not None:
                        return price
            except (json.JSONDecodeError, TypeError):
                continue  # Ignore scripts that aren't valid JSON

        # --- End of new JSON parsing logic ---

        # 2. Fallback to searching HTML text if JSON search fails
        candidates = []
        # Regex to find price-like numbers (e.g., 1,234.56, $123.45, 1.234,56)
        price_regex = re.compile(r'(?:\$|AUD|€|£|USD)?\s*\d{1,3}(?:[,.]\d{3})*(?:[,.]\d{2})?')
        
        for text_node in soup.find_all(string=True):
            # Avoid script and style tags
            if text_node.parent.name in ['script', 'style', 'head', 'title', 'meta', '[document]']:
                continue

            # Find all price-like strings in the text node
            for match in price_regex.finditer(text_node):
                price_text = match.group(0)
                score = 0
                
                # Clean the price text for parsing
                cleaned_price_text = re.sub(r'[^\d,.]', '', price_text)
                if not cleaned_price_text:
                    continue

                # Scoring based on context
                parent = text_node.parent
                parent_text = parent.get_text().lower() if parent else ""
                
                # 1. Check for keywords in surrounding text
                if any(keyword in parent_text for keyword in ['price', 'sale', 'now', 'was', 'total', 'aud', '$']):
                    score += 2
                
                # 2. Check for class names in parent tags
                for p in [parent] + list(parent.parents) if parent else []:
                    if p and p.has_attr('class'):
                        class_names = ' '.join(p['class']).lower()
                        if any(keyword in class_names for keyword in ['price', 'amount', 'cost', 'sale']):
                            score += 3
                
                # 3. Penalize if it's likely part of a larger number or irrelevant string
                if "off" in parent_text or "%" in parent_text:
                    score -= 2
                
                try:
                    # Use a robust parsing function
                    price_value = parse_float(cleaned_price_text)
                    if price_value > 0:
                        candidates.append({'price': price_value, 'score': score, 'text': price_text})
                except (ValueError, TypeError):
                    continue

        if not candidates:
            _LOGGER.warning("No price candidates found on seller page: %s", url)
            return None

        # Select the best candidate based on score
        # To handle cases where multiple candidates have the same high score,
        # we can add a secondary sorting criterion, e.g., preferring larger values
        # as they are more likely to be the main product price.
        candidates.sort(key=lambda x: (x['score'], x['price']), reverse=True)
        
        best_candidate = candidates[0]
        return best_candidate['price']
    except (RequestException, Timeout) as e:
        _LOGGER.error("Network error fetching seller page %s: %s", url, e)
        return None
    except Exception as e:
        _LOGGER.error("Unexpected error fetching/parsing seller page %s: %s", url, e)
        return None


async def transform_raw_product_data(raw_data: dict, product_id: str, item_url: str) -> ItemData:
    """
    Transforms raw product data into an ItemData object, including seller page price validation.
    """
    offers = raw_data.get('offers', [])
    lowest_price_value = None
    lowest_currency_value = ''
    seller_product_url = None
    status_value = ItemStatus.INACTIVE # Initialize status_value to a default

    if offers:
        from custom_components.price_tracker.utilities.parser import parse_float
        def get_base_price(offer):
            base_price = offer.get('base_price', float('inf'))
            # Use parse_float to robustly handle None, empty, or malformed values
            value = parse_float(base_price)
            # If parse_float returns 0.0 for a value that was None or empty, treat as inf for min()
            if base_price is None or (isinstance(base_price, str) and not base_price.strip()):
                return float('inf')
            return value
        lowest_offer = min(offers, key=get_base_price)
        lowest_price_value = lowest_offer.get('base_price')
        lowest_currency_value = lowest_offer.get('currency', 'AUD')
        # Always use the seller_product_url from the lowest-priced offer
        seller_product_url = lowest_offer.get('seller_product_url')
        if not seller_product_url:
            _LOGGER.error(f"No seller_product_url found in lowest_offer: {lowest_offer}")
            # If no seller_product_url, we cannot validate price, so mark as inactive
            status_value = ItemStatus.INACTIVE
            product_link = ""
        else:
            # Validate price on seller's product page
            seller_page_price = await _fetch_and_parse_seller_price(seller_product_url)
            if seller_page_price is not None and abs(seller_page_price - lowest_price_value) > 0.01: # Allow for minor floating point differences
                _LOGGER.error(f"Price mismatch for product_id={product_id}. BuyWisely price: {lowest_price_value}, Seller page price: {seller_page_price}")
                status_value = ItemStatus.PRICE_MISMATCH
                product_link = seller_product_url # Still use the URL even if price mismatches
            elif seller_page_price is None:
                _LOGGER.error(f"Could not extract price from seller page for product_id={product_id}. Marking as inactive.")
                status_value = ItemStatus.PRICE_MISMATCH # This was my previous fix
                product_link = seller_product_url
            else:
                status_value = ItemStatus.ACTIVE # Price matches or no significant difference
                product_link = seller_product_url

    from custom_components.price_tracker.utilities.parser import parse_float
    price_value = lowest_price_value if lowest_price_value is not None else raw_data.get('price')
    price_value = parse_float(price_value) if price_value is not None else None
    # Always default currency to 'AUD' if missing or empty
    currency_value = (lowest_currency_value or raw_data.get('currency') or 'AUD')
    brand_value = raw_data.get('brand') or ''
    # Robustly extract product name from multiple possible fields
    name_fields = ['title', 'name', 'product']
    name_value = None
    for field in name_fields:
        name_raw = raw_data.get(field)
        if isinstance(name_raw, str) and name_raw.strip():
            name_value = name_raw.strip()
            break
    if not name_value:
        name_value = 'UNKNOWN'
        _LOGGER.warning(f"Product name not found in any of {name_fields}, defaulting to 'UNKNOWN'. raw_data keys: {list(raw_data.keys())}")
    image_value = raw_data.get('image') or ''
    # Set status to INACTIVE if price is None or 0.0, or if not in stock
    # This logic is now partially superseded by seller page validation, but still relevant for initial extraction
    if status_value == ItemStatus.ACTIVE and (raw_data.get('availability') != 'In Stock' or price_value in (None, 0.0)):
        status_value = ItemStatus.INACTIVE

    def is_valid_seller_url(url):
        if not url or not isinstance(url, str):
            return False
        url = url.strip()
        if any(url.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp", ".tiff"]):
            return False
        if "buywisely.com.au" in url.lower():
            return False
        if not url.startswith("http"):
            return False
        return True

    # Always use the seller_product_url for BuyWisely
    extracted_url = seller_product_url
    if is_valid_seller_url(extracted_url):
        product_link = extracted_url
    else:
        product_link = ""
        _LOGGER.error(f"No valid seller product URL found in offers for product_id={product_id}. Extraction failure.")

    price = ItemPriceData(price=price_value, currency=currency_value) if price_value is not None and currency_value else ItemPriceData(price=0.0, currency="")

    result = ItemData(
        id=product_id,
        name=name_value,
        brand=brand_value,
        url=product_link or "",
        status=status_value,
        price=price,
        image=image_value,
        category=ItemCategoryData(None),
    )
    return result
