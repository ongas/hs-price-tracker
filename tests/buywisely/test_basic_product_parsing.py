from custom_components.price_tracker.services.buywisely.parser import parse_product
from custom_components.price_tracker.datas.item import ItemStatus


from unittest.mock import patch
import logging

async def mock_fetch_price_func(url, expected_price):
    return expected_price

@patch(
    "custom_components.price_tracker.services.buywisely.data_transformer._fetch_and_parse_seller_price",
    new=mock_fetch_price_func
)
async def test_parse_product_basic():
    html = (
        '<html><body><script id="__NEXT_DATA__" type="application/json">'
        '{"props":{"pageProps":{"product":{"title":"Direct Parse Test","slug":"direct-parse-test","availability":"In Stock","offers":[{"base_price":50.00, "seller_product_url":"http://example.com/product/direct-parse-test", "created_at":"$D2025-09-28T22:34:51.002Z", "seller":{"shopback":null, "cashrewards":null}}],"image":"http://example.com/direct_parse.jpg"}}}}'
        "</script></body></html>"
    )
    result = await parse_product(html)
    logging.warning(f"PARSED RESULT: {result}")
    assert result["name"] == "Direct Parse Test", f"Name mismatch: {result.get('name')}"
    assert (
        result["price"]["price"] == 50.0
    ), f"Price mismatch: {result['price']['price']}"
    assert (
        result["image"] == "http://example.com/direct_parse.jpg"
    ), f"Image mismatch: {result.get('image')}"
    assert (
        result["price"]["currency"] == "AUD"
    ), f"Currency mismatch: {result['price']['currency']}"
    assert (
        result["status"] == ItemStatus.ACTIVE
    ), f"Status mismatch: {result.get('status')}"
