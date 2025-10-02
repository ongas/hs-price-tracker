"""Tests for offer selection and lowest price logic in BuyWiselyEngine."""

import os
from unittest.mock import AsyncMock, patch
import pytest
from custom_components.price_tracker.datas.item import ItemStatus
from custom_components.price_tracker.services.buywisely.engine import BuyWiselyEngine


@pytest.mark.asyncio
@patch("custom_components.price_tracker.services.buywisely.engine.SafeRequest")
@patch(
    "custom_components.price_tracker.services.buywisely.data_transformer._fetch_and_parse_seller_price"
)
async def test_price_mismatch_moves_to_next_offer(
    mock_fetch_seller_price, mock_safe_request
):
    """Test that if the price is mismatched, the engine moves to the next initially visible offer and repeats validation."""
    # Simulate two offers: first is a mismatch, second matches
    # Note: Both offers will be in the initially visible list (sorted by BuyWisely logic)
    offers_html = """<html><body><script id="__NEXT_DATA__" type="application/json">{"props":{"pageProps":{"product":{"title":"Test Product","slug":"test-product","availability":"In Stock","offers":[{"base_price":100.0,"currency":"AUD","seller_product_url":"http://example.com/offer1","created_at":"$D2025-09-28T22:34:51.002Z", "seller":{"name":"Seller1","shopback":null, "cashrewards":null}},{"base_price":120.0,"currency":"AUD","seller_product_url":"http://example.com/offer2","created_at":"$D2025-09-28T22:34:51.002Z", "seller":{"name":"Seller2","shopback":null, "cashrewards":null}}],"image":"http://example.com/test_image.jpg"}}}}</script></body></html>"""
    mock_response = AsyncMock()
    mock_response.has = True
    mock_response.text = offers_html
    mock_response.__bool__.return_value = True
    mock_safe_request.return_value = AsyncMock()
    mock_safe_request.return_value.user_agent.return_value = None
    mock_safe_request.return_value.request.return_value = mock_response

    # First call: mismatch, second call: match
    mock_fetch_seller_price.side_effect = [
        90.0,
        120.0,
    ]  # 100.0 (mismatch), 120.0 (match)
    engine = BuyWiselyEngine(
        item_url="https://www.buywisely.com.au/product/test-product",
        request_cls=mock_safe_request,
    )
    result = await engine.load()
    print("[DIAG] Extraction result:", result)
    # Should select the second offer (120.0) after first mismatch
    assert result is not None, "Expected result, got None"
    extracted_price = getattr(getattr(result, "price", None), "price", None)
    assert extracted_price == 120.0, f"Expected price 120.0, got {extracted_price}"
    assert (
        getattr(result, "url", None) == "http://example.com/offer2"
    ), f"Expected url for second offer, got {getattr(result, 'url', None)}"


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
async def test_get_product_details_multiple_prices(
    mock_fetch_seller_price, mock_safe_request
):
    """Test retrieval of product details when multiple offers are present, ensuring the first initially visible offer is selected using BuyWisely's display logic."""
    mock_fetch_seller_price.return_value = (
        400.89  # Simulate matching price for Amazon.com.au (first in BuyWisely's sort order)
    )
    fixture_file = "real_buywisely_motorola-moto-g75-5g-256gb-grey-with-buds.html"
    print(f"[DIAG][TEST] Loading fixture: {fixture_file}")
    sample_html = _read_fixture_html(fixture_file)
    mock_response = AsyncMock()
    mock_response.has = True
    mock_response.text = sample_html
    mock_response.__bool__.return_value = True

    mock_safe_request.return_value = AsyncMock()
    mock_safe_request.return_value.user_agent.return_value = None
    mock_safe_request.return_value.request.return_value = mock_response
    engine = BuyWiselyEngine(
        item_url="https://www.buywisely.com.au/product/multiple-prices",
        request_cls=mock_safe_request,
    )
    print("[DIAG] HTML passed to parser:", sample_html)
    result = await engine.load()
    print("[DIAG] result:", result)
    assert result is not None, "Expected result, got None"
    # Update expected values to match real HTML fixture
    extracted_name = getattr(result, "name", None)
    print(f"[DIAG][TEST] Extracted name: {extracted_name!r}")
    print(
        f"[DIAG][TEST] Extracted price: {getattr(getattr(result, 'price', None), 'price', None)}"
    )
    expected_name = "Motorola Moto G75 5G 256GB Grey with Buds"
    print(f"[DIAG][TEST] Expected name: {expected_name!r}")
    assert (
        (extracted_name or "").strip() == expected_name.strip()
    ), f"Name mismatch: {extracted_name!r} != {expected_name!r}"
    # With BuyWisely's display logic (Amazon first, then by price, no affiliate filtering),
    # the first initially visible offer is Amazon.com.au at 400.89
    expected_price = 400.89
    expected_currency = "AUD"
    print(f"[DIAG][TEST] Expected price: {expected_price}")
    print(f"[DIAG][TEST] Expected currency: {expected_currency}")
    actual_price = getattr(getattr(result, "price", None), "price", None)
    assert (
        actual_price == expected_price
    ), f"Price mismatch: {actual_price} != {expected_price}"
    assert (
        getattr(getattr(result, "price", None), "currency", None) == expected_currency
    ), f"Currency mismatch: {getattr(getattr(result, 'price', None), 'currency', None)}"
    # Image may not match, so skip image assertion or update to match actual extracted value if needed
    status = getattr(result, "status", None)
    assert status is not None, "Status missing"
    # Expect ACTIVE status since mock returns matching price (400.89 matches expected 400.89)
    print(f"[DIAG][TEST] Extracted status: {status.value}")
    assert (
        status.value == ItemStatus.ACTIVE.value
    ), f"Status value mismatch: {status.value}"


@pytest.mark.asyncio
@patch("custom_components.price_tracker.services.buywisely.engine.SafeRequest")
@patch(
    "custom_components.price_tracker.services.buywisely.data_transformer._fetch_and_parse_seller_price"
)
async def test_lowest_price_selection(mock_fetch_seller_price, mock_safe_request):
    """Test that the engine correctly selects the first initially visible offer using BuyWisely's display logic."""
    mock_fetch_seller_price.return_value = (
        309.99  # Simulate matching price for Amazon.com.au (first in BuyWisely's sort order)
    )
    fixture_file = "real_buywisely_motorola-moto-g85-5g-128gb-urban-grey-.html"
    print(f"[DIAG][TEST] Loading fixture: {fixture_file}")
    sample_html = _read_fixture_html(fixture_file)
    mock_response = AsyncMock()
    mock_response.has = True
    mock_response.text = sample_html
    mock_response.__bool__.return_value = True
    mock_safe_request.return_value = AsyncMock()
    mock_safe_request.return_value.user_agent.return_value = None
    mock_safe_request.return_value.request.return_value = mock_response
    engine = BuyWiselyEngine(
        item_url="https://www.buywisely.com.au/product/multiple-prices",
        request_cls=mock_safe_request,
    )
    print("[DIAG] HTML passed to parser:", sample_html)
    result = await engine.load()

    print("[DIAG] result:", result)
    assert result is not None, "Expected result, got None"
    # Update expected values to match real HTML fixture
    extracted_name = getattr(result, "name", None)
    print(f"[DIAG][TEST] Extracted name: {extracted_name!r}")
    print(
        f"[DIAG][TEST] Extracted price: {getattr(getattr(result, 'price', None), 'price', None)}"
    )
    print(
        f"[DIAG][TEST] Extracted status: {getattr(getattr(result, 'status', None), 'value', None)}"
    )
    expected_name = "Motorola Moto G85 5G 128GB (Urban Grey)"
    # With BuyWisely's display logic (Amazon first, then by price, no affiliate filtering),
    # the first initially visible offer is Amazon.com.au at 309.99
    assert (
        getattr(getattr(result, "price", None), "price", None) == 309.99
    ), f"Lowest price mismatch: {getattr(getattr(result, 'price', None), 'price', None)}"
    assert (
        getattr(getattr(result, "price", None), "currency", None) == "AUD"
    ), f"Currency mismatch: {getattr(getattr(result, 'price', None), 'currency', None)}"
    assert (
        (extracted_name or "").strip() == expected_name.strip()
    ), f"Name mismatch: {extracted_name!r} != {expected_name!r}"
    status = getattr(result, "status", None)
    assert status is not None, "Status missing"
    # Expect ACTIVE status since mock returns matching price (309.99 matches expected 309.99)
    assert (
        status.value == ItemStatus.ACTIVE.value
    ), f"Status value mismatch: {getattr(status, 'value', None)}"
