from custom_components.price_tracker.services.buywisely.hydration_parser import _clean_date_placeholders

def test_clean_date_placeholders_basic():
    """Test cleaning of a single $D date placeholder."""
    input_string = '{"date": "$D2024-01-01T12:00:00Z"}'
    expected_string = '{"date": "2024-01-01T12:00:00Z"}'
    assert _clean_date_placeholders(input_string) == expected_string

def test_clean_date_placeholders_multiple():
    """Test cleaning of multiple $D date placeholders."""
    input_string = '{"start": "$D2023-01-01T00:00:00Z", "end": "$D2023-12-31T23:59:59Z"}'
    expected_string = '{"start": "2023-01-01T00:00:00Z", "end": "2023-12-31T23:59:59Z"}'
    assert _clean_date_placeholders(input_string) == expected_string

def test_clean_date_placeholders_no_match():
    """Test with no $D date placeholders."""
    input_string = '{"name": "product", "price": 100}'
    expected_string = '{"name": "product", "price": 100}'
    assert _clean_date_placeholders(input_string) == expected_string

def test_clean_date_placeholders_empty_string():
    """Test with an empty string."""
    input_string = ""
    expected_string = ""
    assert _clean_date_placeholders(input_string) == expected_string
