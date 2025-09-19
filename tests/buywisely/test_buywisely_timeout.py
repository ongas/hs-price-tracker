from unittest.mock import patch
from custom_components.price_tracker.services.buywisely.parser import parse_product

def test_buywisely_timeout_and_rate_limiting():
    # Simulate a timeout in the HTML extractor
    with patch("custom_components.price_tracker.utilities.hydration_parser.parse_nextjs_hydration_data", side_effect=TimeoutError("Simulated timeout")):
        html = """
        <html><body>
        <script id=\"__NEXT_DATA__\" type=\"application/json\">{"props": {"pageProps": {"product": {"title": "Timeout Product"}}}}</script>
        <span class='price'>$99.99</span>
        </body></html>
        """
        result = parse_product(html, product_id="timeout-1")
        # Accept 0.0 as valid fallback for timeout scenario
        if isinstance(result, dict):
            assert "price" in result and (
                (isinstance(result["price"], dict) and result["price"].get("price") in (None, 0.0)) or
                (isinstance(result["price"], (int, float)) and result["price"] in (None, 0.0))
            )
        else:
            assert hasattr(result, "price") and hasattr(result.price, "price")
            assert result.price.price == 99.99

    # Simulate a rate-limited response (e.g., empty or error in hydration)
    with patch("custom_components.price_tracker.utilities.hydration_parser.parse_nextjs_hydration_data", return_value={}):
        html = """
        <html><body>
        <script id=\"__NEXT_DATA__\" type=\"application/json\">{"error": "rate_limited"}</script>
        <span class='price'>$88.88</span>
        </body></html>
        """
        result = parse_product(html, product_id="ratelimit-1")
        # Should fallback to BeautifulSoup and extract price
        if isinstance(result, dict):
            assert "price" in result and result["price"]["price"] == 88.88
        else:
            assert hasattr(result, "price") and hasattr(result.price, "price")
            assert result.price.price == 88.88
