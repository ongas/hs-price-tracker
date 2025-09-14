import pytest
from custom_components.price_tracker.services.buywisely.parser import parse_product

def test_buywisely_missing_unexpected_data():
    # Hydration with missing required fields (no title, no offers)
    missing_fields_html = """
    <html><body>
    <script id="__NEXT_DATA__" type="application/json">{"props": {"pageProps": {"product": {}}}}</script>
    </body></html>
    """
    result = parse_product(missing_fields_html, product_id="missing-fields-1")
    # Should fallback to defaults, name should be 'UNKNOWN', price 0.0
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

    # Hydration with offers list empty
    empty_offers_html = """
    <html><body>
    <script id="__NEXT_DATA__" type="application/json">{"props": {"pageProps": {"product": {"title": "Test Product", "offers": []}}}}</script>
    </body></html>
    """
    result = parse_product(empty_offers_html, product_id="empty-offers-1")
    # Should fallback to price 0.0, status INACTIVE
    if isinstance(result, dict):
        assert result.get("name") == "Test Product"
        assert "price" in result and (
            (isinstance(result["price"], dict) and result["price"].get("price") in (None, 0.0)) or
            (isinstance(result["price"], (int, float)) and result["price"] in (None, 0.0))
        )
    else:
        assert hasattr(result, "name") and result.name == "Test Product"
        assert hasattr(result, "price") and hasattr(result.price, "price")
        assert result.price.price in (None, 0.0)
