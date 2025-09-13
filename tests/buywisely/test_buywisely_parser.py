from custom_components.price_tracker.services.buywisely.parser import parse_product

def test_parser():
    import pytest
    pytest.skip("This test is skipped because fallback HTML extraction is not supported. The parser requires Next.js hydration data.")

def test_parser_limits_offers_to_ten():
    # This HTML has 15 offers, with the lowest price (5.0) being the 11th offer.
    # The parser should only consider the first 10 offers, so the expected lowest price is 10.0.
    import os
    mock_path = os.path.join(os.path.dirname(__file__), 'mock_buywisely_page_many_offers.html')
    with open(mock_path, 'r', encoding='utf-8') as f:
        html = f.read()
    result = parse_product(html, product_id="test-product-many-offers")
    assert result.name == "Test Product with Many Offers"
    assert result.price.price == 10.0
    assert result.price.currency == "AUD"