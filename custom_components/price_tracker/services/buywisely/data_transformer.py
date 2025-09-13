import logging
from custom_components.price_tracker.datas.item import ItemData, ItemStatus
from custom_components.price_tracker.datas.price import ItemPriceData
from custom_components.price_tracker.datas.category import ItemCategoryData
from urllib.parse import urlparse

_LOGGER = logging.getLogger(__name__)

def transform_raw_product_data(raw_data: dict, product_id: str, item_url: str) -> ItemData:
    offers = raw_data.get('offers', [])
    lowest_price_value = None
    lowest_currency_value = ''

    if offers:
        def get_base_price(offer):
            try:
                return float(offer.get('base_price', float('inf')))
            except ValueError:
                return float('inf')
        
        lowest_offer = min(offers, key=get_base_price)
        lowest_price_value = lowest_offer.get('base_price')
        lowest_currency_value = lowest_offer.get('currency', 'AUD') # Assuming default currency is AUD if not specified in offer

    price_value = lowest_price_value if lowest_price_value is not None else raw_data.get('price')
    currency_value = lowest_currency_value or raw_data.get('currency') or ''
    brand_value = raw_data.get('brand') or ''
    name_value = raw_data.get('title') or 'UNKNOWN'
    image_value = raw_data.get('image') or ''
    status_value = ItemStatus.ACTIVE if raw_data.get('availability') == 'In Stock' else ItemStatus.INACTIVE

    extracted_url_or_slug = raw_data.get('url')

    if extracted_url_or_slug and (extracted_url_or_slug.startswith("http://") or extracted_url_or_slug.startswith("https://")):
        # It's a full URL, use it directly
        product_link = extracted_url_or_slug
    elif extracted_url_or_slug:
        # It's a slug, construct full URL using item_url's base
        # Assuming item_url is always a full URL and represents the base domain
        parsed_item_url = urlparse(item_url)
        base_url = f"{parsed_item_url.scheme}://{parsed_item_url.netloc}"
        product_link = f"{base_url}/product/{extracted_url_or_slug}"
    else:
        # No URL or slug extracted, fall back to item_url
        product_link = item_url

    # Requirement 4: If the seller's product page URL contains 'buywisely', it indicates a failure.
    if "buywisely" in product_link: # Simplified check
        _LOGGER.warning(f"[DataTransformer] Detected BuyWisely URL as product link, indicating extraction failure: {product_link}")
        product_link = "" # Explicitly set to empty string for failure

    price = ItemPriceData(price=price_value, currency=currency_value) if price_value is not None and currency_value else ItemPriceData(price=0.0, currency="")

    result = ItemData(
        id=product_id,
        name=name_value,
        brand=brand_value,
        url=product_link,
        status=status_value,
        price=price,
        image=image_value,
        category=ItemCategoryData(None),
    )
    _LOGGER.info(f"[DIAG][DataTransformer] Returning ItemData: {result}, as_dict: {getattr(result, 'dict', 'no dict') if hasattr(result, 'dict') else str(result)}")
    return result
