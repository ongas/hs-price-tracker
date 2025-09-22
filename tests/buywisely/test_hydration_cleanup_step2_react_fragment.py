from custom_components.price_tracker.services.buywisely.hydration_parser import _clean_react_fragment_literal

def test_clean_react_fragment_literal_basic():
    """Test cleaning of a single "$Sreact.fragment" literal."""
    input_string = '{"type": "$Sreact.fragment", "content": "some content"}'
    expected_string = '{"type": "react.fragment", "content": "some content"}'
    assert _clean_react_fragment_literal(input_string) == expected_string

def test_clean_react_fragment_literal_multiple():
    """Test cleaning of multiple "$Sreact.fragment" literals."""
    input_string = '{"item1": "$Sreact.fragment", "item2": "$Sreact.fragment"}'
    expected_string = '{"item1": "react.fragment", "item2": "react.fragment"}'
    assert _clean_react_fragment_literal(input_string) == expected_string

def test_clean_react_fragment_literal_no_match():
    """Test with no "$Sreact.fragment" literal."""
    input_string = '{"name": "product", "price": 100}'
    expected_string = '{"name": "product", "price": 100}'
    assert _clean_react_fragment_literal(input_string) == expected_string

def test_clean_react_fragment_literal_empty_string():
    """Test with an empty string."""
    input_string = ""
    expected_string = ""
    assert _clean_react_fragment_literal(input_string) == expected_string
