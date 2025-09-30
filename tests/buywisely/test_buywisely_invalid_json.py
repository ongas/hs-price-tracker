from custom_components.price_tracker.services.buywisely.parser import parse_product

async def test_buywisely_invalid_json_in_hydration():
    # HTML with invalid JSON in hydration block
    invalid_json_html = """
    <html><body>
    <script id="__NEXT_DATA__" type="application/json">{invalid: json, missing: 'quotes'}</script>
    <span class='price'>$88.88</span>
    </body></html>
    """
    result = await parse_product(invalid_json_html, product_id="invalid-json-1")
    # Should fallback to BeautifulSoup and extract price
    if isinstance(result, dict):
        assert "price" in result and isinstance(result["price"], dict)
        assert result["price"]["price"] == 88.88
        assert result["price"]["currency"] == "AUD"
    else:
        assert hasattr(result, "price") and hasattr(result.price, "price")
        assert result.price.price == 88.88
        assert hasattr(result.price, "currency") and result.price.currency == "AUD"

    # HTML with unexpected JSON structure in hydration block
    unexpected_json_html = """
    <html><body>
    <script id="__NEXT_DATA__" type="application/json">{"foo": {"bar": 123}}</script>
    <span class='price'>$77.77</span>
    </body></html>
    """
    result = await parse_product(unexpected_json_html, product_id="unexpected-json-1")
    # Should fallback to BeautifulSoup and extract price
    if isinstance(result, dict):
        assert "price" in result and isinstance(result["price"], dict)
        assert result["price"]["price"] == 77.77
        assert result["price"]["currency"] == "AUD"
    else:
        assert hasattr(result, "price") and hasattr(result.price, "price")
        assert result.price.price == 77.77
        assert hasattr(result.price, "currency") and result.price.currency == "AUD"
