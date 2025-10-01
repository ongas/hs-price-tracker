from custom_components.price_tracker.services.buywisely.parser import parse_product


async def test_parse_product_euro_currency():
    html = (
        '<html><body><script id="__NEXT_DATA__" type="application/json">'
        '{"props":{"pageProps":{"product":{"title":"Euro Product","slug":"euro-product","availability":"In Stock","offers":[{"base_price":25.99,"currency":"EUR"}],"image":"http://example.com/euro_product.jpg"}}}}'
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
