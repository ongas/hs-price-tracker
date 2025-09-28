"""Tests for BuyWiselyEngine URL parsing and validation."""

import pytest
from custom_components.price_tracker.services.buywisely.engine import BuyWiselyEngine
from custom_components.price_tracker.components.error import InvalidItemUrlError

def test_parse_id_valid_url():
    """Test that a valid BuyWisely product URL is parsed correctly."""
    valid_url = "https://www.buywisely.com.au/product/example-product-name"
    result = BuyWiselyEngine.parse_id(valid_url)
    assert result == {"product_id": "example-product-name"}

def test_parse_id_valid_url_with_query_params():
    """Test that a valid BuyWisely product URL with query parameters is parsed correctly."""
    valid_url = ("https://www.buywisely.com.au/product/another-product-name?"  # Line break for pylint
                 "param1=value1&param2=value2")
    result = BuyWiselyEngine.parse_id(valid_url)
    assert result == {"product_id": "another-product-name"}

def test_parse_id_invalid_url_no_product_segment():
    """Test that an invalid BuyWisely URL without a '/product/' segment raises an error."""
    invalid_url = "https://www.buywisely.com.au/category/some-category"
    with pytest.raises(InvalidItemUrlError, match="Bad item_url"):
        BuyWiselyEngine.parse_id(invalid_url)

def test_parse_id_invalid_url_malformed():
    """Test that a malformed URL raises an error."""
    malformed_url = "not-a-valid-url"
    with pytest.raises(InvalidItemUrlError, match="Invalid domain in item_url"):
        BuyWiselyEngine.parse_id(malformed_url)

def test_parse_id_invalid_url_different_domain():
    """Test that a URL from a different domain raises an error."""
    different_domain_url = "https://www.google.com/product/some-product"
    with pytest.raises(InvalidItemUrlError, match="Invalid domain in item_url"):
        BuyWiselyEngine.parse_id(different_domain_url)
