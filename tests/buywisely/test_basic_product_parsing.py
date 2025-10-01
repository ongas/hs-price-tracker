from unittest.mock import patch
from custom_components.price_tracker.services.buywisely.parser import parse_product
from custom_components.price_tracker.datas.item import ItemStatus


@patch(
    "custom_components.price_tracker.services.buywisely.data_transformer._fetch_and_parse_seller_price",
    return_value=50.00,
)
async def test_parse_product_basic(mock_fetch_seller_price):
    html = (
        '<html><body><script id="__NEXT_DATA__" type="application/json">'
        '{"props":{"pageProps":{"product":{"title":"Direct Parse Test","slug":"direct-parse-test","availability":"In Stock","offers":[{"base_price":50.00, "seller_product_url":"http://example.com/product"}],"image":"http://example.com/direct_parse.jpg"}}}}'
        "</script></body></html>"
    )
    result = await parse_product(html)
    assert result["name"] == "Direct Parse Test", f"Name mismatch: {result.get('name')}"
    assert (
        result["price"]["price"] == 50.00
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
