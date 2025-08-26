def test_parse_product_with_crawl4ai_data():
    html = """
    <html>
    <body>
        <h2>Should be ignored</h2>
        <h3>$999.99</h3>
        <img class="product-image" alt="Product Image" src="http://example.com/should_be_ignored.jpg">
    </body>
    </html>
    """
    crawl4ai_data = {
        "products": [
            {
                "product_status": {"lowest_price": "123.45"},
                "media": {"images": ["http://example.com/crawl4ai_image.jpg"]}
            }
        ]
    }
    result = parse_product(html, crawl4ai_data)
    assert result["price"] == 123.45
    assert result["image"] == "http://example.com/crawl4ai_image.jpg"
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from custom_components.price_tracker.services.buywisely.engine import BuyWiselyEngine
from custom_components.price_tracker.services.buywisely.parser import parse_product
from custom_components.price_tracker.utilities.safe_request import SafeRequestMethod



@pytest.mark.asyncio
@patch('custom_components.price_tracker.services.buywisely.engine.SafeRequest')
async def test_get_product_details_success(mock_safe_request):
    # Sample HTML content that matches the parser's selectors
    sample_html = """
    <html>
    <body>
        <h2>Test Product Title</h2>
        <h3>$123.45</h3>
        <img class="product-image" alt="Product Image" src="http://example.com/test_image.jpg">
    </body>
    </html>
    """
    # Configure the mock SafeRequest instance
    mock_instance = mock_safe_request.return_value # This is the instance of SafeRequest
    mock_response_data = AsyncMock()
    mock_response_data.text = sample_html
    mock_response_data.has = True
    mock_instance.request = AsyncMock(return_value=mock_response_data)

    engine = BuyWiselyEngine()
    url = "http://example.com/product"
    
    result = await engine.get_product_details(url)

    assert result == {
        "title": "Test Product Title",
        "price": 123.45,
        "image": "http://example.com/test_image.jpg",
        "currency": "AUD",
        "availability": "In Stock"
    }
    # Assert that SafeRequest.request was called
    mock_instance.request.assert_called_once_with(
        method=SafeRequestMethod.GET,
        url=url,
    )

@pytest.mark.asyncio
@patch('custom_components.price_tracker.services.buywisely.engine.SafeRequest')
async def test_get_product_details_no_price(mock_safe_request):
    sample_html = """
    <html>
    <body>
        <h2>Another Product</h2>
        <img class="product-image" alt="Product Image" src="http://example.com/another_image.jpg">
    </body>
    </html>
    """
    mock_instance = mock_safe_request.return_value
    mock_response_data = AsyncMock()
    mock_response_data.text = sample_html
    mock_response_data.has = True
    mock_instance.request = AsyncMock(return_value=mock_response_data)

    engine = BuyWiselyEngine()
    url = "http://example.com/another_product"
    
    result = await engine.get_product_details(url)

    assert result == {
        "title": "Another Product",
        "price": None,
        "image": "http://example.com/another_image.jpg",
        "currency": "AUD", # Default currency is still AUD even if no price
        "availability": "Out of Stock"
    }
    mock_instance.request.assert_called_once_with(
        method=SafeRequestMethod.GET,
        url=url,
    )

@pytest.mark.asyncio
@patch('custom_components.price_tracker.services.buywisely.engine.SafeRequest')
async def test_get_product_details_multiple_prices(mock_safe_request):
    sample_html = """
    <html>
    <body>
        <h2>Product with Multiple Prices</h2>
        <h3>$100.00</h3>
        <h3>$99.50</h3>
        <img class="product-image" alt="Product Image" src="http://example.com/multiple_prices.jpg">
    </body>
    </html>
    """
    mock_instance = mock_safe_request.return_value
    mock_response_data = AsyncMock()
    mock_response_data.text = sample_html
    mock_response_data.has = True
    mock_instance.request = AsyncMock(return_value=mock_response_data)

    engine = BuyWiselyEngine()
    url = "http://example.com/multiple_prices"
    
    result = await engine.get_product_details(url)

    assert result == {
        "title": "Product with Multiple Prices",
        "price": 99.50, # Expects the minimum price
        "image": "http://example.com/multiple_prices.jpg",
        "currency": "AUD",
        "availability": "In Stock"
    }
    mock_instance.request.assert_called_once_with(
        method=SafeRequestMethod.GET,
        url=url,
    )

# Test cases for parse_product directly
def test_parse_product_basic():
    html = """
    <html>
    <body>
        <h2>Direct Parse Test</h2>
        <h3>$50.00</h3>
        <img class="product-image" alt="Product Image" src="http://example.com/direct_parse.jpg">
    </body>
    </html>
    """
    result = parse_product(html)
    assert result["title"] == "Direct Parse Test"
    assert result["price"] == 50.00
    assert result["image"] == "http://example.com/direct_parse.jpg"
    assert result["currency"] == "AUD"
    assert result["availability"] == "In Stock"

def test_parse_product_euro_currency():
    html = """
    <html>
    <body>
        <h2>Euro Product</h2>
        <h3>€25.99</h3>
        <img class="product-image" alt="Product Image" src="http://example.com/euro_product.jpg">
    </body>
    </html>
    """
    result = parse_product(html)
    assert result["price"] == 25.99
    assert result["currency"] == "EUR"

def test_parse_product_no_image():
    html = """
    <html>
    <body>
        <h2>No Image Product</h2>
        <h3>$75.00</h3>
    </body>
    </html>
    """
    result = parse_product(html)
    assert result["image"] is None

@pytest.mark.asyncio
@patch('custom_components.price_tracker.services.buywisely.engine.SafeRequest')
async def test_buywisely_engine_uses_crawl4ai(monkeypatch):
    # Patch AsyncWebCrawler.arun to simulate crawl4ai extraction
    with patch("crawl4ai.AsyncWebCrawler.arun", new_callable=AsyncMock) as mock_arun:
        mock_arun.return_value = {
            "products": [
                {"product_status": {"lowest_price": "99.99"}, "media": {"images": ["http://example.com/crawl4ai.jpg"]}}
            ]
        }
        engine = BuyWiselyEngine(extraction_method="advanced")
        # Patch SafeRequest to avoid real network calls
        with patch("custom_components.price_tracker.services.buywisely.engine.SafeRequest") as mock_safe_request:
            mock_instance = mock_safe_request.return_value
            mock_response_data = AsyncMock()
            mock_response_data.text = "<html><h2>Should be ignored</h2></html>"
            mock_response_data.has = True
            mock_instance.request = AsyncMock(return_value=mock_response_data)
            url = "http://example.com/product"
            # Actually call get_product_details and await it
            result = await engine.get_product_details(url)
            # Ensure crawl4ai extraction was called
            assert mock_arun.called, "crawl4ai AsyncWebCrawler.arun was not called for advanced extraction method"
