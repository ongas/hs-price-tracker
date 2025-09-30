"""Tests for price validation logic in BuyWiselyEngine."""
import os
from unittest.mock import AsyncMock, patch
import pytest

from custom_components.price_tracker.datas.item import ItemStatus
from custom_components.price_tracker.services.buywisely.engine import BuyWiselyEngine

def _read_fixture_html(filename: str) -> str:
    """Helper to read HTML content from a fixture file."""
    filepath = os.path.join(os.path.dirname(__file__), "fixtures", filename)
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


@pytest.mark.asyncio
@patch("custom_components.price_tracker.services.buywisely.engine.SafeRequest")
@patch("custom_components.price_tracker.services.buywisely.data_transformer._fetch_and_parse_seller_price")
async def test_price_must_be_greater_than_zero(mock_fetch_seller_price, mock_safe_request):
    """Test that loading a product with a zero or missing price raises a ValueError."""
    # Test case 1: Valid product with non-zero price
    sample_html_valid_price = _read_fixture_html("buywisely_product_details_success.html")
    mock_response_valid = AsyncMock()
    mock_response_valid.has = True
    mock_response_valid.text = sample_html_valid_price
    mock_response_valid.__bool__.return_value = True

    mock_safe_request.return_value = AsyncMock()
    mock_safe_request.return_value.user_agent.return_value = None
    mock_safe_request.return_value.request.return_value = mock_response_valid
    mock_fetch_seller_price.return_value = 10.00  # Simulate matching price
    engine_valid = BuyWiselyEngine(item_url="https://www.buywisely.com.au/product/valid-product", request_cls=mock_safe_request)
    result_valid = await engine_valid.load()
    assert result_valid is not None
    assert getattr(getattr(result_valid, 'price', None), 'price', None) > 0.0, "Price should be greater than 0 for a valid product"

    # Test case 2: Product with zero price - should raise an exception
    sample_html_zero_price = _read_fixture_html("buywisely_product_details_zero_price.html")
    mock_response_zero = AsyncMock()
    mock_response_zero.has = True
    mock_response_zero.text = sample_html_zero_price
    mock_response_zero.__bool__.return_value = True

    mock_safe_request.return_value = AsyncMock()
    mock_safe_request.return_value.user_agent.return_value = None
    mock_safe_request.return_value.request.return_value = mock_response_zero
    mock_fetch_seller_price.return_value = 0.00  # Simulate matching price
    engine_zero = BuyWiselyEngine(item_url="https://www.buywisely.com.au/product/zero-price-product", request_cls=mock_safe_request)

    # Expect an exception to be raised when loading a product with a zero price
    with pytest.raises(ValueError, match="Extracted price cannot be zero or less."):
        await engine_zero.load()

    # Test case 3: Product with missing price - should raise an exception
    sample_html_missing_price = _read_fixture_html("buywisely_product_details_missing_price.html")
    mock_response_missing = AsyncMock()
    mock_response_missing.has = True
    mock_response_missing.text = sample_html_missing_price
    mock_response_missing.__bool__.return_value = True

    mock_safe_request.return_value = AsyncMock()
    mock_safe_request.return_value.user_agent.return_value = None
    mock_safe_request.return_value.request.return_value = mock_response_missing
    mock_fetch_seller_price.return_value = None  # Simulate missing price
    engine_missing = BuyWiselyEngine(item_url="https://www.buywisely.com.au/product/missing-price-product", request_cls=mock_safe_request)

    # Expect an exception to be raised when loading a product with a missing price
    with pytest.raises(ValueError, match="Extracted price cannot be zero or less."):
        await engine_missing.load()
