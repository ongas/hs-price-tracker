"""Tests for basic product data extraction from BuyWiselyEngine."""

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
@patch(
    "custom_components.price_tracker.services.buywisely.data_transformer._fetch_and_parse_seller_price"
)
async def test_get_product_details_success(mock_fetch_seller_price, mock_safe_request):
    """Test successful retrieval of product details from a BuyWisely page."""
    mock_fetch_seller_price.return_value = 123.45  # Simulate matching price
    sample_html = _read_fixture_html("buywisely_product_details_success.html")
    mock_response = AsyncMock()
    mock_response.has = True
    mock_response.text = sample_html
    mock_response.__bool__.return_value = True

    mock_safe_request.return_value = AsyncMock()
    mock_safe_request.return_value.user_agent.return_value = None
    mock_safe_request.return_value.request.return_value = mock_response
    engine = BuyWiselyEngine(
        item_url="https://www.buywisely.com.au/product/test-product",
        request_cls=mock_safe_request,
    )
    print("[DIAG] HTML passed to parser:", sample_html)
    result = await engine.load()
    print("[DIAG] result:", result)
    assert result is not None, "Expected result, got None"
    assert (
        getattr(result, "name", None) == "Test Product Title"
    ), f"Name mismatch: {getattr(result, 'name', None)}"
    assert (
        getattr(getattr(result, "price", None), "price", None) == 123.45
    ), f"Price mismatch: {getattr(getattr(result, 'price', None), 'price', None)}"
    assert (
        getattr(getattr(result, "price", None), "currency", None) == "AUD"
    ), f"Currency mismatch: {getattr(getattr(result, 'price', None), 'currency', None)}"
    assert (
        getattr(result, "image", None) == "http://example.com/test_image.jpg"
    ), f"Image mismatch: {getattr(result, 'image', None)}"
    status = getattr(result, "status", None)
    assert status is not None, "Status missing"
    assert (
        status.value == ItemStatus.ACTIVE.value
    ), f"Status value mismatch: {status.value}"
