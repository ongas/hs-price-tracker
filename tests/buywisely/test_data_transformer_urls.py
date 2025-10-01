import pytest
from custom_components.price_tracker.services.buywisely.data_transformer import (
    transform_raw_product_data,
)


# Mock raw_data for testing
@pytest.fixture
def mock_raw_data():
    return {
        "title": "Test Product",
        "image": "http://example.com/image.jpg",
        "currency": "AUD",
        "availability": "In Stock",
        "offers": [
            {
                "base_price": 100.00,
                "currency": "AUD",
                "seller_product_url": "http://seller.com/product1",
                "shipping": 5.00,
            }
        ],
    }


@pytest.mark.asyncio
async def test_is_valid_seller_url_valid_url(mock_raw_data):
    # Access the is_valid_seller_url function from within transform_raw_product_data
    # This is a bit of a hack, but necessary since it's a nested function
    # In a real scenario, this function would ideally be a standalone helper
    # or part of a class for easier testing.
    # For now, we'll call transform_raw_product_data and then inspect the URL it sets.
    # This test primarily checks the outcome of the URL validation.

    # Test a valid seller URL
    mock_raw_data["offers"][0]["seller_product_url"] = "http://valid-seller.com/product"
    item_data = await transform_raw_product_data(
        mock_raw_data, "test_product_id", "http://buywisely.com.au/product/test"
    )
    assert item_data.url == "http://valid-seller.com/product"


@pytest.mark.asyncio
async def test_is_valid_seller_url_buywisely_url(mock_raw_data):
    # Test a buywisely.com.au URL (should be invalid as a seller URL)
    mock_raw_data["offers"][0]["seller_product_url"] = (
        "http://buywisely.com.au/product/test"
    )
    item_data = await transform_raw_product_data(
        mock_raw_data, "test_product_id", "http://buywisely.com.au/product/test"
    )
    assert item_data.url == ""


@pytest.mark.asyncio
async def test_is_valid_seller_url_image_url(mock_raw_data):
    # Test an image URL (should be invalid)
    mock_raw_data["offers"][0]["seller_product_url"] = "http://seller.com/image.jpg"
    item_data = await transform_raw_product_data(
        mock_raw_data, "test_product_id", "http://buywisely.com.au/product/test"
    )
    assert item_data.url == ""


@pytest.mark.asyncio
async def test_is_valid_seller_url_malformed_url(mock_raw_data):
    # Test a malformed URL (should be invalid)
    mock_raw_data["offers"][0]["seller_product_url"] = "invalid-url"
    item_data = await transform_raw_product_data(
        mock_raw_data, "test_product_id", "http://buywisely.com.au/product/test"
    )
    assert item_data.url == ""


@pytest.mark.asyncio
async def test_is_valid_seller_url_none_url(mock_raw_data):
    # Test a None URL (should be invalid)
    mock_raw_data["offers"][0]["seller_product_url"] = None
    item_data = await transform_raw_product_data(
        mock_raw_data, "test_product_id", "http://buywisely.com.au/product/test"
    )
    assert item_data.url == ""


@pytest.mark.asyncio
async def test_is_valid_seller_url_empty_string_url(mock_raw_data):
    # Test an empty string URL (should be invalid)
    mock_raw_data["offers"][0]["seller_product_url"] = ""
    item_data = await transform_raw_product_data(
        mock_raw_data, "test_product_id", "http://buywisely.com.au/product/test"
    )
    assert item_data.url == ""
