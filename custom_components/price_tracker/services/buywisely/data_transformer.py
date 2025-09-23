import logging
from custom_components.price_tracker.datas.item import ItemData, ItemStatus
from custom_components.price_tracker.datas.price import ItemPriceData
from custom_components.price_tracker.datas.category import ItemCategoryData

_LOGGER = logging.getLogger(__name__)

def transform_raw_product_data(raw_data: dict, product_id: str, item_url: str) -> ItemData:
    _LOGGER.warning(f"[DIAG][data_transformer] Incoming raw_data: {raw_data}")
    offers = raw_data.get('offers', [])
    lowest_price_value = None
    lowest_currency_value = ''
    seller_product_url = None

    if offers:
        _LOGGER.info(f"[DIAG][data_transformer] Offers count: {len(offers)}")
        for idx, offer in enumerate(offers):
            url_candidate = offer.get('seller_product_url')
            _LOGGER.info(f"[DIAG][data_transformer] Offer {idx} seller_product_url: {url_candidate}")
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
            _LOGGER.error(f"[DIAG][data_transformer] No seller_product_url found in lowest_offer: {lowest_offer}")

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
            _LOGGER.info(f"[DIAG][data_transformer] Product name found in field '{field}': {name_value}")
            break
    if not name_value:
        name_value = 'UNKNOWN'
        _LOGGER.warning(f"[DIAG][data_transformer] Product name not found in any of {name_fields}, defaulting to 'UNKNOWN'. raw_data keys: {list(raw_data.keys())}")
    image_value = raw_data.get('image') or ''
    # Set status to INACTIVE if price is None or 0.0, or if not in stock
    price_val_for_status = price_value if price_value is not None else 0.0
    if raw_data.get('availability') == 'In Stock' and price_val_for_status not in (None, 0.0):
        status_value = ItemStatus.ACTIVE
    else:
        status_value = ItemStatus.INACTIVE

    def is_valid_seller_url(url):
        if not url or not isinstance(url, str):
            _LOGGER.info(f"[DIAG][data_transformer] is_valid_seller_url: url is None or not a string: {url}")
            return False
        url = url.strip()
        if any(url.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp", ".tiff"]):
            _LOGGER.info(f"[DIAG][data_transformer] is_valid_seller_url: url ends with image extension: {url}")
            return False
        if "buywisely.com.au" in url.lower():
            _LOGGER.info(f"[DIAG][data_transformer] is_valid_seller_url: url contains buywisely.com.au: {url}")
            return False
        if not url.startswith("http"):
            _LOGGER.info(f"[DIAG][data_transformer] is_valid_seller_url: url does not start with http: {url}")
            return False
        return True

    # Always use the seller_product_url for BuyWisely
    extracted_url = seller_product_url
    _LOGGER.info(f"[DIAG][data_transformer] extracted_url (seller_product_url): {extracted_url}, item_url: {item_url}")
    if is_valid_seller_url(extracted_url):
        product_link = extracted_url
    else:
        product_link = ""
        _LOGGER.error(f"[data_transformer] No valid seller product URL found in offers for product_id={product_id}. Extraction failure.")
    _LOGGER.info(f"[DIAG][data_transformer] Final url for ItemData: {product_link}")

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
    _LOGGER.info(f"[DIAG][DataTransformer] Returning ItemData: {result}, as_dict: {getattr(result, 'dict', 'no dict') if hasattr(result, 'dict') else str(result)}")
    return result
