from unittest.mock import patch
from custom_components.price_tracker.services.buywisely.parser import parse_product

async def mock_fetch_price_func(url, expected_price):
    return expected_price

@patch(
    "custom_components.price_tracker.services.buywisely.data_transformer._fetch_and_parse_seller_price",
    new=mock_fetch_price_func
)
async def test_parse_product_euro_currency():
    html = (
        '<html><body><script id="__NEXT_DATA__" type="application/json">'
        '{"props":{"pageProps":{"product":{"title":"Euro Product","slug":"euro-product","availability":"In Stock","offers":[{"base_price":25.99,"currency":"EUR","seller_product_url":"http://example.com/euro-product", "created_at":"$D2025-09-28T22:34:51.002Z", "seller":{"shopback":null, "cashrewards":null}}],"image":"http://example.com/euro_product.jpg"}}}}'
        "</script></body></html>"
    )
    result = await parse_product(html)
    print("[DIAG] result:", result)
    assert (
        result["price"]["price"] == 25.99
    ), f"Price mismatch: {result['price']['price']}"
    assert (
        result["price"]["currency"] == "EUR"
    ), f"Currency mismatch: {result['price']['currency']}"
