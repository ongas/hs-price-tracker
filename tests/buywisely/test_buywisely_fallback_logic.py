from custom_components.price_tracker.services.buywisely.parser import parse_product

def test_buywisely_fallback_logic():
    # Hydration block present but empty, price in HTML
    html = """
    <html><body>
    <script id=\"__NEXT_DATA__\" type=\"application/json\">{}</script>
    <span class='price'>$55.55</span>
    </body></html>
    """
    result = parse_product(html, product_id="fallback-1")
    # Should fallback to BeautifulSoup and extract price
    if isinstance(result, dict):
        assert "price" in result and result["price"]["price"] == 55.55
    else:
        assert hasattr(result, "price") and hasattr(result.price, "price")
        assert result.price.price == 55.55

    # Hydration and price element both missing
    html_no_price = "<html><body><h1>No price here</h1></body></html>"
    result = parse_product(html_no_price, product_id="fallback-2")
    # Should fallback and return price 0.0
    if isinstance(result, dict):
        assert "price" in result and (
            (isinstance(result["price"], dict) and result["price"].get("price") in (None, 0.0)) or
            (isinstance(result["price"], (int, float)) and result["price"] in (None, 0.0))
        )
    else:
        assert hasattr(result, "price") and hasattr(result.price, "price")
        assert result.price.price in (None, 0.0)
