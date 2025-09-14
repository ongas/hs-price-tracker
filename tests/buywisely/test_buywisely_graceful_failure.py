from custom_components.price_tracker.services.buywisely.parser import parse_product

def test_buywisely_graceful_failure():
    # Completely unparseable HTML (no hydration, no price, no fallback)
    html = "<html><body><h1>Nothing here</h1></body></html>"
    result = parse_product(html, product_id="fail-1")
    # Should not crash, should return sensible defaults (price 0.0, name 'UNKNOWN')
    if isinstance(result, dict):
        assert result.get("name") == "UNKNOWN"
        assert "price" in result and (
            (isinstance(result["price"], dict) and result["price"].get("price") in (None, 0.0)) or
            (isinstance(result["price"], (int, float)) and result["price"] in (None, 0.0))
        )
    else:
        assert hasattr(result, "name") and result.name == "UNKNOWN"
        assert hasattr(result, "price") and hasattr(result.price, "price")
        assert result.price.price in (None, 0.0)
