import logging
from custom_components.price_tracker.datas.item import ItemData, ItemStatus
from custom_components.price_tracker.datas.price import ItemPriceData
from custom_components.price_tracker.datas.category import ItemCategoryData
from custom_components.price_tracker.datas.delivery import DeliveryData # Import DeliveryData

_LOGGER = logging.getLogger(__name__)

def transform_raw_product_data(raw_data: dict, product_id: str, item_url: str) -> ItemData:
    _LOGGER.debug(f"[DIAG][data_transformer] Input raw_data: {raw_data}")
    _LOGGER.debug(f"[DIAG][data_transformer] Input product_id: {product_id}")
    _LOGGER.debug(f"[DIAG][data_transformer] Input item_url: {item_url}")
    offers = raw_data.get('offers', [])
    lowest_price_value = None
    lowest_currency_value = ''
    seller_product_url = None

    if offers:
        _LOGGER.info(f"[DIAG][data_transformer] Offers count: {len(offers)}")
        for idx, offer in enumerate(offers):
            url_candidate = offer.get('seller_product_url')
            _LOGGER.info(f"[DIAG][data_transformer] Offer {idx} seller_product_url: {url_candidate}")
        def get_base_price(offer):
            try:
                return float(offer.get('base_price', float('inf')))
            except ValueError:
                return float('inf')
        lowest_offer = min(offers, key=get_base_price)
        lowest_price_value = lowest_offer.get('base_price')
        lowest_currency_value = lowest_offer.get('currency', 'AUD')
        # Always use the seller_product_url from the lowest-priced offer
        seller_product_url = lowest_offer.get('seller_product_url')
        if not seller_product_url:
            _LOGGER.error(f"[DIAG][data_transformer] No seller_product_url found in lowest_offer: {lowest_offer}")

    # Use base_price from raw_data for the main price, and delivery_price for delivery
    price_value = lowest_price_value if lowest_price_value is not None else raw_data.get('price') # This is now the base price from html_extractor
    delivery_price_value = raw_data.get('delivery_price')
    currency_value = lowest_currency_value or raw_data.get('currency') or ''
    brand_value = raw_data.get('brand') or ''
    name_value = raw_data.get('title') or 'UNKNOWN'
    image_value = raw_data.get('image') or ''
    status_value = ItemStatus.ACTIVE if raw_data.get('availability') == 'In Stock' else ItemStatus.INACTIVE

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
    elif raw_data.get('url') and is_valid_seller_url(raw_data.get('url')):
        product_link = raw_data.get('url')
        _LOGGER.info(f"[DIAG][data_transformer] Using URL from raw_data: {product_link}")
    else:
        product_link = ""
        _LOGGER.error(f"[data_transformer] No valid seller product URL found in offers or raw_data for product_id={product_id}. Extraction failure.")
    _LOGGER.info(f"[DIAG][data_transformer] Final url for ItemData: {product_link}")

    price = ItemPriceData(price=price_value, original_price=price_value, currency=currency_value) if price_value is not None else ItemPriceData(currency="")
    delivery = DeliveryData(price=delivery_price_value) if delivery_price_value is not None else DeliveryData()

    result = ItemData(
        id=product_id,
        name=name_value,
        brand=brand_value,
        url=product_link or "",
        status=status_value,
        price=price,
        image=image_value,
        category=ItemCategoryData(None),
        delivery=delivery,
    )
    _LOGGER.info(f"[DIAG][DataTransformer] Returning ItemData: {result}, as_dict: {getattr(result, 'dict', 'no dict') if hasattr(result, 'dict') else str(result)}")
    return result
