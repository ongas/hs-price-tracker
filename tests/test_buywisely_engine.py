# Example: Mock test using real HTML from buywisely.com.au
import pytest
from unittest.mock import AsyncMock, patch
from custom_components.price_tracker.services.buywisely.engine import BuyWiselyEngine
from custom_components.price_tracker.datas.item import ItemStatus

@pytest.mark.asyncio
@patch('custom_components.price_tracker.services.buywisely.engine.SafeRequest')
async def test_real_html_product_parsing(mock_safe_request):
    # Realistic HTML snippet from BuyWisely Sony WH-1000XM4 product page
    sample_html = """
    <html>
    <body>
        <h2>Sony - WH-1000XM4 Wireless Noise Cancelling Headphones - Black</h2>
        <h3>$348.00</h3>
        <img class="product-image" alt="Product Image" src="https://buywisely.com.au/product/sony-wh-1000xm4-wireless-noise-cancelling-headphones-black-1">
    </body>
    </html>
    """
    mock_instance = mock_safe_request.return_value
    mock_response_data = AsyncMock()
    mock_response_data.text = sample_html
    mock_response_data.has = True
    mock_instance.request = AsyncMock(return_value=mock_response_data)

    engine = BuyWiselyEngine(item_url="https://buywisely.com.au/product/sony-wh-1000xm4-wireless-noise-cancelling-headphones-black-1?id=12345")
    result = await engine.load()

    if result is None:
        print("DIAGNOSTIC: result is None")
        assert False, "BuyWiselyEngine.load() returned None for real HTML test."
    else:
        print(f"DIAGNOSTIC: name={getattr(result, 'name', None)}, price={getattr(getattr(result, 'price', None), 'price', None)}, currency={getattr(getattr(result, 'price', None), 'currency', None)}, image={getattr(result, 'image', None)}, status={getattr(result, 'status', None)}")
        assert getattr(result, 'name', None) == "Sony - WH-1000XM4 Wireless Noise Cancelling Headphones - Black"
        assert getattr(getattr(result, 'price', None), 'price', None) == 348.00
        assert getattr(getattr(result, 'price', None), 'currency', None) == "AUD"
        assert getattr(result, 'image', None) == "https://buywisely.com.au/product/sony-wh-1000xm4-wireless-noise-cancelling-headphones-black-1"
        assert getattr(result, 'status', None) == ItemStatus.ACTIVE
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from custom_components.price_tracker.services.buywisely.engine import BuyWiselyEngine
from custom_components.price_tracker.services.buywisely.parser import parse_product
from custom_components.price_tracker.utilities.safe_request import SafeRequestMethod
from custom_components.price_tracker.datas.item import ItemStatus


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

    engine = BuyWiselyEngine(item_url="http://example.com/product?id=123")
    
    result = await engine.load()

    if result is None:
        print("DIAGNOSTIC: result is None (test_get_product_details_success)")
        assert False, "BuyWiselyEngine.load() returned None for test_get_product_details_success."
    else:
        print(f"DIAGNOSTIC: name={getattr(result, 'name', None)}, price={getattr(getattr(result, 'price', None), 'price', None)}, currency={getattr(getattr(result, 'price', None), 'currency', None)}, image={getattr(result, 'image', None)}, status={getattr(result, 'status', None)}")
        assert getattr(result, 'name', None) == "Test Product Title"
        assert getattr(getattr(result, 'price', None), 'price', None) == 123.45
        assert getattr(getattr(result, 'price', None), 'currency', None) == "AUD"
        assert getattr(result, 'image', None) == "http://example.com/test_image.jpg"
        assert getattr(result, 'status', None) == ItemStatus.ACTIVE

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

    engine = BuyWiselyEngine(item_url="http://example.com/another_product?id=123")
    
    result = await engine.load()

    if result is None:
        print("DIAGNOSTIC: result is None (test_get_product_details_no_price)")
        assert False, "BuyWiselyEngine.load() returned None for test_get_product_details_no_price."
    else:
        print(f"DIAGNOSTIC: name={getattr(result, 'name', None)}, price={getattr(getattr(result, 'price', None), 'price', None)}, currency={getattr(getattr(result, 'price', None), 'currency', None)}, image={getattr(result, 'image', None)}, status={getattr(result, 'status', None)}")
        assert getattr(result, 'name', None) == "Another Product"
    assert getattr(getattr(result, 'price', None), 'price', None) == 0.0
    assert getattr(getattr(result, 'price', None), 'currency', None) == ""
    assert getattr(result, 'status', None) == ItemStatus.INACTIVE

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

    engine = BuyWiselyEngine(item_url="http://example.com/multiple_prices?id=123")
    
    result = await engine.load()

    if result is None:
        print("DIAGNOSTIC: result is None (test_get_product_details_multiple_prices)")
        assert False, "BuyWiselyEngine.load() returned None for test_get_product_details_multiple_prices."
    else:
        print(f"DIAGNOSTIC: name={getattr(result, 'name', None)}, price={getattr(getattr(result, 'price', None), 'price', None)}, currency={getattr(getattr(result, 'price', None), 'currency', None)}, image={getattr(result, 'image', None)}, status={getattr(result, 'status', None)}")
        assert getattr(result, 'name', None) == "Product with Multiple Prices"
        assert getattr(getattr(result, 'price', None), 'price', None) == 99.50
        assert getattr(getattr(result, 'price', None), 'currency', None) == "AUD"
        assert getattr(result, 'image', None) == "http://example.com/multiple_prices.jpg"
        assert getattr(result, 'status', None) == ItemStatus.ACTIVE

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
        engine = BuyWiselyEngine(item_url="http://example.com/product?id=123")
        # Patch SafeRequest to avoid real network calls
        with patch("custom_components.price_tracker.services.buywisely.engine.SafeRequest") as mock_safe_request:
            mock_instance = mock_safe_request.return_value
            mock_response_data = AsyncMock()
            mock_response_data.text = "<html><h2>Should be ignored</h2></html>"
            mock_response_data.has = True
            mock_instance.request = AsyncMock(return_value=mock_response_data)
            # Actually call get_product_details and await it
            result = await engine.load()
            # Ensure crawl4ai extraction was called
            assert mock_arun.called, "crawl4ai AsyncWebCrawler.arun was not called for advanced extraction method"