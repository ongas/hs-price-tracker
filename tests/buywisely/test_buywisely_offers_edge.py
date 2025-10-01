from custom_components.price_tracker.services.buywisely.parser import parse_product


async def test_buywisely_offers_edge_cases():
    # More than 10 offers, lowest price is not the first in the list
    offers = [
        {"base_price": 20.0, "currency": "AUD"},
        {"base_price": 30.0, "currency": "AUD"},
        {"base_price": 40.0, "currency": "AUD"},
        {"base_price": 50.0, "currency": "AUD"},
        {"base_price": 60.0, "currency": "AUD"},
        {"base_price": 70.0, "currency": "AUD"},
        {"base_price": 80.0, "currency": "AUD"},
        {"base_price": 90.0, "currency": "AUD"},
        {"base_price": 100.0, "currency": "AUD"},
        {"base_price": 110.0, "currency": "AUD"},
        {"base_price": 5.0, "currency": "AUD"},  # Should be ignored
    ]
    offers_json = ",".join([str(offer).replace("'", '"') for offer in offers])
    html = f"""
    <html><body>
    <script id=\"__NEXT_DATA__\" type=\"application/json\">{{\"props\": {{\"pageProps\": {{\"product\": {{\"title\": \"Test Product\", \"offers\": [{offers_json}]}}}}}}}}</script>
    </body></html>
    """
    result = await parse_product(html, product_id="offers-edge-1")
    # All current offers considered, so lowest price should be 5.0 (but ignored if business logic excludes zero/invalid)
    if isinstance(result, dict):
        assert result.get("name") == "Test Product"
        assert "price" in result and result["price"]["price"] == 5.0
    else:
        assert hasattr(result, "name") and result.name == "Test Product"
        assert hasattr(result, "price") and hasattr(result.price, "price")
        assert result.price.price == 5.0

    # Offer with missing price/currency
    html_missing = """
    <html><body>
    <script id=\"__NEXT_DATA__\" type=\"application/json\">{"props": {"pageProps": {"product": {"title": "Test Product 2", "offers": [{"foo": 1}]}}}}</script>
    </body></html>
    """
    result = await parse_product(html_missing, product_id="offers-edge-2")
    # Should fallback to price 0.0
    if isinstance(result, dict):
        assert result.get("name") == "Test Product 2"
        assert "price" in result and (
            (
                isinstance(result["price"], dict)
                and result["price"].get("price") in (None, 0.0)
            )
            or (
                isinstance(result["price"], (int, float))
                and result["price"] in (None, 0.0)
            )
        )
    else:
        assert hasattr(result, "name") and result.name == "Test Product 2"
        assert hasattr(result, "price") and hasattr(result.price, "price")
        assert result.price.price in (None, 0.0)
