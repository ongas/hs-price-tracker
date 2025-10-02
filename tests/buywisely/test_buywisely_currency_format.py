from custom_components.price_tracker.services.buywisely.parser import parse_product


async def test_buywisely_currency_price_format_handling():
    # Unusual currency symbol
    html_currency = """
    <html><body>
    <script id=\"__NEXT_DATA__\" type=\"application/json\">{"props": {"pageProps": {"product": {"title": "Product X", "offers": [{"base_price": 12.34, "currency": "XYZ$", "created_at": "$D2025-09-28T22:34:51.002Z", "seller":{"shopback":null, "cashrewards":null}}]}}}}</script>
    </body></html>
    """
    result = await parse_product(html_currency, product_id="currency-1")
    if isinstance(result, dict):
        assert result.get("name") == "Product X"
        # Now uses offer price even without seller_product_url
        assert "price" in result and result["price"]["price"] == 12.34
        assert result["price"]["currency"] == "XYZ$"
    else:
        assert hasattr(result, "name") and result.name == "Product X"
        assert hasattr(result, "price") and hasattr(result.price, "price")
        # Now uses offer price even without seller_product_url
        assert result.price.price == 12.34
        assert hasattr(result.price, "currency") and result.price.currency == "XYZ$"

    # Price as string with comma
    html_price_str = """
    <html><body>
    <script id=\"__NEXT_DATA__\" type=\"application/json\">{"props": {"pageProps": {"product": {"title": "Product Y", "offers": [{"base_price": "1,234.56", "currency": "AUD", "created_at": "$D2025-09-28T22:34:51.002Z", "seller":{"shopback":null, "cashrewards":null}}]}}}}</script>
    </body></html>
    """
    result = await parse_product(html_price_str, product_id="currency-2")
    if isinstance(result, dict):
        assert result.get("name") == "Product Y"
        # String prices like "1,234.56" are parsed correctly by parse_float
        assert "price" in result and result["price"]["price"] == 1234.56
        assert result["price"]["currency"] == "AUD"
    else:
        assert hasattr(result, "name") and result.name == "Product Y"
        assert hasattr(result, "price") and hasattr(result.price, "price")
        # String prices like "1,234.56" are parsed correctly by parse_float
        assert result.price.price == 1234.56
        assert hasattr(result.price, "currency") and result.price.currency == "AUD"
