"""Tests for price validation logic in BuyWiselyEngine."""

import os
from unittest.mock import AsyncMock, patch
import pytest

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
async def test_price_must_be_greater_than_zero(
    mock_fetch_seller_price, mock_safe_request
):
    """Test that loading a product with a zero or missing price raises a ValueError."""
    # Test case 1: Valid product with non-zero price
    sample_html_valid_price = _read_fixture_html(
        "buywisely_product_details_success.html"
    )
    mock_response_valid = AsyncMock()
    mock_response_valid.has = True
    mock_response_valid.text = sample_html_valid_price
    mock_response_valid.__bool__.return_value = True

    mock_safe_request.return_value = AsyncMock()
    mock_safe_request.return_value.user_agent.return_value = None
    mock_safe_request.return_value.request.return_value = mock_response_valid
    mock_fetch_seller_price.return_value = 10.00  # Simulate matching price
    engine_valid = BuyWiselyEngine(
        item_url="https://www.buywisely.com.au/product/valid-product",
        request_cls=mock_safe_request,
    )
    result_valid = await engine_valid.load()
    assert result_valid is not None
    extracted_price = getattr(getattr(result_valid, "price", None), "price", None)
    assert (
        extracted_price is not None
    ), "Extracted price should not be None for a valid product"
    assert extracted_price > 0.0, "Price should be greater than 0 for a valid product"

    # Test case 2: Product with zero price - should raise an exception
    sample_html_zero_price = _read_fixture_html(
        "buywisely_product_details_zero_price.html"
    )
    mock_response_zero = AsyncMock()
    mock_response_zero.has = True
    mock_response_zero.text = sample_html_zero_price
    mock_response_zero.__bool__.return_value = True

    mock_safe_request.return_value = AsyncMock()
    mock_safe_request.return_value.user_agent.return_value = None
    mock_safe_request.return_value.request.return_value = mock_response_zero
    mock_fetch_seller_price.return_value = 0.00  # Simulate matching price
    engine_zero = BuyWiselyEngine(
        item_url="https://www.buywisely.com.au/product/zero-price-product",
        request_cls=mock_safe_request,
    )

    # Expect an exception to be raised when loading a product with a zero price
    with pytest.raises(ValueError, match="Extracted price cannot be zero or less."):
        await engine_zero.load()

    # Test case 3: Product with missing price - should raise an exception
    sample_html_missing_price = _read_fixture_html(
        "buywisely_product_details_missing_price.html"
    )
    mock_response_missing = AsyncMock()
    mock_response_missing.has = True
    mock_response_missing.text = sample_html_missing_price
    mock_response_missing.__bool__.return_value = True

    mock_safe_request.return_value = AsyncMock()
    mock_safe_request.return_value.user_agent.return_value = None
    mock_safe_request.return_value.request.return_value = mock_response_missing
    mock_fetch_seller_price.return_value = None  # Simulate missing price
    engine_missing = BuyWiselyEngine(
        item_url="https://www.buywisely.com.au/product/missing-price-product",
        request_cls=mock_safe_request,
    )

    # Expect an exception to be raised when loading a product with a missing price
    with pytest.raises(ValueError, match="Extracted price cannot be zero or less."):
        await engine_missing.load()

    @pytest.mark.asyncio
    @patch("custom_components.price_tracker.services.buywisely.engine.SafeRequest")
    @patch(
        "custom_components.price_tracker.services.buywisely.data_transformer._fetch_and_parse_seller_price"
    )
    async def test_price_extraction_with_real_seller_page(
        mock_fetch_seller_price, mock_safe_request
    ):
        """Test price extraction using a real seller page HTML fixture."""
        sample_html_real = _read_fixture_html(
            "real_buywisely_motorola-moto-g75-5g-256gb-grey-with-buds.html"
        )
        mock_response_real = AsyncMock()
        mock_response_real.has = True
        mock_response_real.text = sample_html_real
        mock_response_real.__bool__.return_value = True

        mock_safe_request.return_value = AsyncMock()
        mock_safe_request.return_value.user_agent.return_value = None
        mock_safe_request.return_value.request.return_value = mock_response_real
        mock_fetch_seller_price.return_value = (
            399.00  # Simulate expected price from seller page
        )
        engine_real = BuyWiselyEngine(
            item_url="https://www.buywisely.com.au/product/real-fixture-test",
            request_cls=mock_safe_request,
        )
        result_real = await engine_real.load()
        print("[DIAG] Extraction result from real seller page:", result_real)
        assert (
            result_real is not None
        ), "Expected result, got None from real seller page"
        extracted_price_obj = getattr(result_real, "price", None)
        assert (
            extracted_price_obj is not None
        ), "Expected a price object from real seller page"
        extracted_price = getattr(extracted_price_obj, "price", None)
        assert (
            extracted_price is not None
        ), "Extracted price should not be None for real seller page"
        assert (
            extracted_price > 0.0
        ), "Price should be greater than 0 for real seller page"
        print("[DIAG] Extracted price:", extracted_price)
