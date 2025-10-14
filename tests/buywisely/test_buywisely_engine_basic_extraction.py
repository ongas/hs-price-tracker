"""Tests for basic product data extraction from BuyWiselyEngine."""

import os
from unittest.mock import AsyncMock, patch, Mock
import logging
import pytest

from custom_components.price_tracker.datas.item import ItemStatus
from custom_components.price_tracker.services.buywisely.engine import BuyWiselyEngine

_LOGGER = logging.getLogger(__name__)


def _read_fixture_html(filename: str) -> str:
    """Helper to read HTML content from a fixture file."""
    filepath = os.path.join(os.path.dirname(__file__), "fixtures", filename)
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


_SAFE_REQUEST_PATH = (
    "custom_components.price_tracker.utilities."
    "safe_request.SafeRequest"
)
_FETCH_SELLER_PRICE_PATH = (
    "custom_components.price_tracker.services."
    "buywisely.data_transformer."
    "_fetch_and_parse_seller_price"
)

@pytest.mark.asyncio
@patch(_SAFE_REQUEST_PATH)
@patch(_FETCH_SELLER_PRICE_PATH)
async def test_get_product_details_success(mock_fetch_seller_price, mock_safe_request):
    """Test successful retrieval of product details from a BuyWisely page."""

    mock_hass = AsyncMock()
    mock_hass.async_add_executor_job.side_effect = lambda func, *args, **kwargs: func(*args, **kwargs)

    mock_fetch_seller_price.return_value = 123.45 # Directly return the expected price
    mock_safe_request.return_value.user_agent = Mock(return_value=None)

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
        hass=mock_hass,
    )
    result = await engine.load()
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
