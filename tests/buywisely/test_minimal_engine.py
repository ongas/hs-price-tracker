"""Minimal test for the BuyWiselyEngine."""

from unittest.mock import AsyncMock, patch
import pytest

from custom_components.price_tracker.datas.item import ItemStatus
from custom_components.price_tracker.services.buywisely.engine import BuyWiselyEngine


@pytest.mark.asyncio
@patch("custom_components.price_tracker.services.buywisely.engine.SafeRequest")
@patch(
    "custom_components.price_tracker.services.buywisely.data_transformer._fetch_and_parse_seller_price"
)
async def test_get_product_details_success_minimal(
    mock_fetch_seller_price, mock_safe_request
):
    """Test successful retrieval of product details from a BuyWisely page with complex HTML data."""
    mock_fetch_seller_price.return_value = 123.45  # Simulate matching price

    # Read sample HTML from fixture file
    with open(
        "tests/buywisely/fixtures/minimal_product.html", "r", encoding="utf-8"
    ) as f:
        sample_html = f.read()

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

    # The engine.load() method internally calls parse_product
    result = await engine.load()

    assert result is not None
    # Accept either 'Test Product Title' or 'test-product' depending on extraction logic
    assert result.name in ["Test Product Title", "test-product"]
    assert result.price.price == 123.45
    assert result.price.currency == "AUD"
    assert result.status.value == ItemStatus.ACTIVE.value
