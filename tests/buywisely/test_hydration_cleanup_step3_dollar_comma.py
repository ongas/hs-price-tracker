from custom_components.price_tracker.services.buywisely.hydration_parser import _clean_dollar_comma_literal

def test_clean_dollar_comma_literal_basic():
    """Test cleaning of a single "$," literal."""
    input_string = '{"value": "$,", "currency": "USD"}'
    expected_string = '{"value": "", "currency": "USD"}'
    assert _clean_dollar_comma_literal(input_string) == expected_string

def test_clean_dollar_comma_literal_multiple():
    """Test cleaning of multiple "$," literals."""
    input_string = '{"item1": "$,", "item2": "$,", "price": "$,",}'
    expected_string = '{"item1": "", "item2": "", "price": "",}'
    assert _clean_dollar_comma_literal(input_string) == expected_string

def test_clean_dollar_comma_literal_no_match():
    """Test with no "$," literal."""
    input_string = '{"name": "product", "price": 100}'
    expected_string = '{"name": "product", "price": 100}'
    assert _clean_dollar_comma_literal(input_string) == expected_string

def test_clean_dollar_comma_literal_empty_string():
    """Test with an empty string."""
    input_string = ""
    expected_string = ""
    assert _clean_dollar_comma_literal(input_string) == expected_string
