from custom_components.price_tracker.services.buywisely.parser import parse_product

async def test_buywisely_malformed_html_and_missing_hydration():
    # Malformed HTML (broken tags, no hydration block)
    malformed_html = "<html><body><div><span class='price'>$99.99</span></div>"
    result = await parse_product(malformed_html, product_id="malformed-1")
    # Should fallback to BeautifulSoup and extract price
    if isinstance(result, dict):
        assert "price" in result and isinstance(result["price"], dict)
        assert result["price"]["price"] == 99.99
        assert result["price"]["currency"] == "AUD"
    else:
        assert hasattr(result, "price") and hasattr(result.price, "price")
        assert result.price.price == 99.99
        assert hasattr(result.price, "currency") and result.price.currency == "AUD"

    # HTML with no hydration block and no price
    no_hydration_html = "<html><body><h1>Product Page</h1></body></html>"
    result = await parse_product(no_hydration_html, product_id="no-hydration-1")
    # Should fallback and not crash, price should be 0.0 (default) and currency empty string
    if isinstance(result, dict):
        # Accept 0.0 as valid fallback for missing price
        assert "price" in result and (
            (isinstance(result["price"], dict) and (result["price"].get("price") in (None, 0.0))) or
            (isinstance(result["price"], (int, float)) and result["price"] in (None, 0.0))
        )
    else:
        # Accept ItemData.price.price == 0.0 as valid fallback
        assert hasattr(result, "price")
        assert hasattr(result.price, "price")
        assert result.price.price in (None, 0.0)
