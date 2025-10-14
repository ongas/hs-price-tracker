import re
import os
from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from homeassistant.core import HomeAssistant
from custom_components.price_tracker.services.buywisely.engine import BuyWiselyEngine
from custom_components.price_tracker.const import DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.loader import IntegrationNotFound

file_path = "/mnt/e/source/personal_repos/homeassistant/custom_components/price_tracker/tests/buywisely/test_buywisely_engine_price_validation.py"

# Read the current content of the file
with open(file_path, "r") as f:
    content = f.read()

# Helper to read HTML content from a fixture file
def _read_fixture_html(filename: str) -> str:
    filepath = os.path.join(os.path.dirname(__file__), "fixtures", filename)
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

# Define the mock function
mock_fetch_price_func_definition = r'''
async def mock_fetch_price_func(url, expected_price):
    return expected_price
'''

# Define the pattern for the old test function
old_test_pattern = r'''@pytest.mark.asyncio
@patch\("custom_components.price_tracker.services.buywisely.engine.SafeRequest"\)
@patch\(
    "custom_components.price_tracker.services.buywisely.data_transformer._fetch_and_parse_seller_price"
\)
async def test_price_must_be_greater_than_zero\(
    mock_fetch_seller_price, mock_safe_request
\):
    """Test that loading a product with a zero or missing price raises a ValueError."""
    # Test case 1: Valid product with non-zero price
    sample_html_valid_price = _read_fixture_html\(
        "buywisely_product_details_success.html"
    \)
    mock_response_valid = AsyncMock\(\)
    mock_response_valid.has = True
    mock_response_valid.text = sample_html_valid_price
    mock_response_valid.__bool__.return_value = True

    mock_safe_request.return_value = AsyncMock\(\)
    mock_safe_request.return_value.user_agent.return_value = None
    mock_safe_request.return_value.request.return_value = mock_response_valid
    mock_fetch_seller_price.return_value = 10.00  # Simulate matching price
    engine_valid = BuyWiselyEngine\(
        item_url="https://www.buywisely.com.au/product/valid-product",
        request_cls=mock_safe_request,
    \)
    result_valid = await engine_valid.load\(\)
    assert result_valid is not None
    extracted_price = getattr\(getattr\(result_valid, "price", None\), "price", None\)
    assert \(
        extracted_price is not None
    \), "Extracted price should not be None for a valid product"
    assert extracted_price > 0.0, "Price should be greater than 0 for a valid product"

    # Test case 2: Product with zero price - should raise an exception
    sample_html_zero_price = _read_fixture_html\(
        "buywisely_product_details_zero_price.html"
    \)
    mock_response_zero = AsyncMock\(\)
    mock_response_zero.has = True
    mock_response_zero.text = sample_html_zero_price
    mock_response_zero.__bool__.return_value = True

    mock_safe_request.return_value = AsyncMock\(\)
    mock_safe_request.return_value.user_agent.return_value = None
    mock_safe_request.return_value.request.return_value = mock_response_zero
    mock_fetch_seller_price.return_value = 0.00  # Simulate matching price
    engine_zero = BuyWiselyEngine\(
        item_url="https://www.buywisely.com.au/product/zero-price-product",
        request_cls=mock_safe_request,
    \)

    # Expect an exception to be raised when loading a product with a zero price
    with pytest.raises\(ValueError, match="Extracted price cannot be zero or less."\):
        await engine_zero.load\(\)

    # Test case 3: Product with missing price - should raise an exception
    sample_html_missing_price = _read_fixture_html\(
        "buywisely_product_details_missing_price.html"
    \)
    mock_response_missing = AsyncMock\(\)
    mock_response_missing.has = True
    mock_response_missing.text = sample_html_missing_price
    mock_response_missing.__bool__.return_value = True

    mock_safe_request.return_value = AsyncMock\(\)
    mock_safe_request.return_value.user_agent.return_value = None
    mock_safe_request.return_value.request.return_value = mock_response_missing
    mock_fetch_seller_price.return_value = None  # Simulate missing price
    engine_missing = BuyWiselyEngine\(
        item_url="https://www.buywisely.com.au/product/missing-price-product",
        request_cls=mock_safe_request,
    \)

    # Expect an exception to be raised when loading a product with a missing price
    with pytest.raises\(ValueError, match="Extracted price cannot be zero or less."\):
        await engine_missing.load\(\)'''

# Define the new test function content
new_test_content = mock_fetch_price_func_definition + r'''
@pytest.mark.asyncio
@patch("custom_components.price_tracker.services.buywisely.engine.SafeRequest")
@patch(
    "custom_components.price_tracker.services.buywisely.data_transformer._fetch_and_parse_seller_price",
    new=mock_fetch_price_func
)
async def test_price_must_be_greater_than_zero(mock_safe_request, hass: HomeAssistant):
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
    engine_valid = BuyWiselyEngine(
        hass=hass,
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
    engine_zero = BuyWiselyEngine(
        hass=hass,
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
    engine_missing = BuyWiselyEngine(
        hass=hass,
        item_url="https://www.buywisely.com.au/product/missing-price-product",
        request_cls=mock_safe_request,
    )

    # Expect an exception to be raised when loading a product with a missing price
    with pytest.raises(ValueError, match="Extracted price cannot be zero or less."):
        await engine_missing.load()'''

# Perform the replacement
# Use re.DOTALL to make '.' match newlines
modified_content = re.sub(old_test_pattern, new_test_content, content, flags=re.DOTALL)

# Write the modified content back to the file
with open(file_path, "w") as f:
    f.write(modified_content)

print("Refactoring of test_price_must_be_greater_than_zero complete.")