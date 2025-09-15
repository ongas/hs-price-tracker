import logging
from custom_components.price_tracker.datas.item import ItemData, ItemStatus
from custom_components.price_tracker.datas.price import ItemPriceData
from custom_components.price_tracker.datas.category import ItemCategoryData

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


    # Use the url field directly. If not present or invalid, set to empty and log error. No fallback to BuyWisely or item_url.
    def is_valid_seller_url(url):
        if not url or not isinstance(url, str):
            return False
        url = url.strip()
        # Exclude image URLs
        if any(url.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp", ".tiff"]):
            return False
        # Exclude BuyWisely URLs
        if "buywisely.com.au" in url.lower():
            return False
        return url.startswith("http")

    extracted_url = raw_data.get('url')
    _LOGGER.info(f"[DIAG][data_transformer] extracted_url: {extracted_url}, item_url: {item_url}")
    product_link = ""
    if is_valid_seller_url(extracted_url):
        product_link = extracted_url
    else:
        # Fallback: use first valid seller_product_url from offers
        offers = raw_data.get('offers', [])
        for idx, offer in enumerate(offers):
            offer_url = offer.get('seller_product_url')
            if is_valid_seller_url(offer_url):
                product_link = offer_url
                _LOGGER.info(f"[DIAG][data_transformer] Fallback to seller_product_url from offer #{idx}: {offer_url}")
                break
        if not product_link:
            _LOGGER.error(f"[data_transformer] No valid seller product URL found for product_id={product_id}. Extraction failure.")
    _LOGGER.info(f"[DIAG][data_transformer] Final url for ItemData: {product_link}")

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
