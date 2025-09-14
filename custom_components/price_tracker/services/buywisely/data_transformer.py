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


    # Use the url field directly, or fallback to first valid seller_product_url from offers
    extracted_url = raw_data.get('url')
    _LOGGER.info(f"[DIAG][data_transformer] extracted_url: {extracted_url}, item_url: {item_url}")
    product_link = extracted_url
    if not product_link:
        offers = raw_data.get('offers', [])
        _LOGGER.info(f"[DIAG][data_transformer] offers for fallback: {offers!r}")
        for idx, offer in enumerate(offers):
            offer_url = offer.get('seller_product_url')
            _LOGGER.info(f"[DIAG][data_transformer] Checking offer #{idx}: {offer!r}")
            if offer_url and 'buywisely' not in offer_url:
                product_link = offer_url
                _LOGGER.info(f"[DIAG][data_transformer] Using seller_product_url from offer #{idx}: {offer_url}")
                break
        else:
            _LOGGER.info(f"[DIAG][data_transformer] No valid seller_product_url found in offers.")
    if not product_link:
        product_link = item_url
        _LOGGER.info(f"[DIAG][data_transformer] Fallback to item_url: {item_url}")
    if product_link and "buywisely" in product_link:
        _LOGGER.warning(f"[DataTransformer] Detected BuyWisely URL as product link, indicating extraction failure: {product_link}")
        product_link = ""
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
