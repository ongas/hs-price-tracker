import logging
from .html_extractor import extract_product_data_from_html
from .data_transformer import transform_raw_product_data

_LOGGER = logging.getLogger(__name__)

def parse_product(html: str, product_id: str | None = None, item_url: str | None = None) -> dict:
    raw_data = extract_product_data_from_html(html)
    return transform_raw_product_data(raw_data, product_id, item_url)
