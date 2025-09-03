import sys
import os
import pytest
from unittest.mock import AsyncMock, patch
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from services.buywisely.engine import BuyWiselyEngine
from datas.item import ItemStatus
from services.buywisely.parser import parse_product

@pytest.mark.asyncio
@patch("custom_components.price_tracker.services.buywisely.engine.SafeRequest")
async def test_real_html_product_parsing(mock_safe_request):
    # ...existing code...
    sample_html = """
    <html>
    <body>
        <h2>Sony - WH-1000XM4 Wireless Noise Cancelling Headphones - Black</h2>
        <h3>$348.00</h3>
        <img class="product-image" alt="Product Image" src="https://buywisely.com.au/product/sony-wh-1000xm4-wireless-noise-cancelling-headphones-black-1">
    </body>
    </html>
    """
    mock_response = AsyncMock()
    mock_response.has = True
    mock_response.text = sample_html
    mock_response.__bool__.return_value = True
    print(f"DIAGNOSTIC: mock_response.has={getattr(mock_response, 'has', None)}")
    print(f"DIAGNOSTIC: mock_response.text={getattr(mock_response, 'text', None)}")
    print(f"DIAGNOSTIC: mock_response.__bool__={mock_response.__bool__()}")
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

    class MockSafeRequest:
        def user_agent(self, *args, **kwargs):
            pass
        async def request(self, *args, **kwargs):
            return mock_response
    engine = BuyWiselyEngine(item_url="https://buywisely.com.au/product/sony-wh-1000xm4-wireless-noise-cancelling-headphones-black-1?id=12345", request_cls=MockSafeRequest)
    print("DIAGNOSTIC: About to call engine.load() with custom mock response")
    from unittest.mock import patch
    mock_response = AsyncMock()
    mock_response.has = True
    mock_response.text = sample_html
    mock_response.__bool__.return_value = True
    mock_instance = mock_safe_request.return_value
    mock_instance.user_agent = lambda *args, **kwargs: None
    mock_instance.request = AsyncMock(return_value=mock_response)
    result = await engine.load()
    print(f"DIAGNOSTIC: engine.load() returned: {result}")
    if result is None:
        print("DIAGNOSTIC: result is None")
        assert False, "BuyWiselyEngine.load() returned None for real HTML test."
    else:
        print(f"DIAGNOSTIC: name={getattr(result, 'name', None)}, price={getattr(getattr(result, 'price', None), 'price', None)}, currency={getattr(getattr(result, 'price', None), 'currency', None)}, image={getattr(result, 'image', None)}, status={getattr(result, 'status', None)}")
        print(f"DIAGNOSTIC: result dict: {getattr(result, 'dict', None) if hasattr(result, 'dict') else str(result)}")
        assert getattr(result, 'name', None) == "Sony - WH-1000XM4 Wireless Noise Cancelling Headphones - Black"
        assert getattr(getattr(result, 'price', None), 'price', None) == 348.00
        assert getattr(getattr(result, 'price', None), 'currency', None) == "AUD"
        assert getattr(result, 'image', None) == "https://buywisely.com.au/product/sony-wh-1000xm4-wireless-noise-cancelling-headphones-black-1"
    status = getattr(result, 'status', None)
    assert status is not None
    assert status.value == ItemStatus.ACTIVE.value
@pytest.mark.asyncio
@patch("custom_components.price_tracker.services.buywisely.engine.SafeRequest")
async def test_get_product_details_success(mock_safe_request):
    # ...existing code...
    sample_html = """
    <html>
    <body>
        <h2>Test Product Title</h2>
        <h3>$123.45</h3>
        <img class="product-image" alt="Product Image" src="http://example.com/test_image.jpg">
    </body>
    </html>
    """
    mock_response = AsyncMock()
    mock_response.has = True
    mock_response.text = sample_html
    mock_response.__bool__.return_value = True
    print(f"DIAGNOSTIC: mock_response.has={getattr(mock_response, 'has', None)}")
    print(f"DIAGNOSTIC: mock_response.text={getattr(mock_response, 'text', None)}")
    print(f"DIAGNOSTIC: mock_response.__bool__={mock_response.__bool__()}")
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

    class MockSafeRequest:
        def user_agent(self, *args, **kwargs):
            pass
        async def request(self, *args, **kwargs):
            return mock_response
    engine = BuyWiselyEngine(item_url="http://example.com/product/test-product", request_cls=MockSafeRequest)
    
    print("DIAGNOSTIC: About to call engine.load() with custom mock response")
    from unittest.mock import patch
    mock_response = AsyncMock()
    mock_response.has = True
    mock_response.text = sample_html
    mock_response.__bool__.return_value = True
    mock_instance = mock_safe_request.return_value
    mock_instance.user_agent = lambda *args, **kwargs: None
    mock_instance.request = AsyncMock(return_value=mock_response)
    result = await engine.load()
    print(f"DIAGNOSTIC: engine.load() returned: {result}")
    assert result is not None
    print(f"DIAGNOSTIC: name={getattr(result, 'name', None)}, price={getattr(getattr(result, 'price', None), 'price', None)}, currency={getattr(getattr(result, 'price', None), 'currency', None)}, image={getattr(result, 'image', None)}, status={getattr(result, 'status', None)}")
    assert getattr(result, 'name', None) == "Test Product Title"
    assert getattr(getattr(result, 'price', None), 'price', None) == 123.45
    assert getattr(getattr(result, 'price', None), 'currency', None) == "AUD"
    assert getattr(result, 'image', None) == "http://example.com/test_image.jpg"
    status = getattr(result, 'status', None)
    assert status is not None
    assert status.value == ItemStatus.ACTIVE.value

@pytest.mark.asyncio
@patch("custom_components.price_tracker.services.buywisely.engine.SafeRequest")
async def test_get_product_details_no_price(mock_safe_request):
    # ...existing code...
    sample_html = """
    <html>
    <body>
        <h2>Another Product</h2>
        <img class="product-image" alt="Product Image" src="http://example.com/another_image.jpg">
    </body>
    </html>
    """
    mock_response = AsyncMock()
    mock_response.has = True
    mock_response.text = sample_html
    mock_response.__bool__.return_value = True
    print(f"DIAGNOSTIC: mock_response.has={getattr(mock_response, 'has', None)}")
    print(f"DIAGNOSTIC: mock_response.text={getattr(mock_response, 'text', None)}")
    print(f"DIAGNOSTIC: mock_response.__bool__={mock_response.__bool__()}")
    sample_html = """
    <html>
    <body>
        <h2>Another Product</h2>
        <img class="product-image" alt="Product Image" src="http://example.com/another_image.jpg">
    </body>
    </html>
    """

    class MockSafeRequest:
        def user_agent(self, *args, **kwargs):
            pass
        async def request(self, *args, **kwargs):
            return mock_response
    engine = BuyWiselyEngine(item_url="http://example.com/product/another-product", request_cls=MockSafeRequest)
    
    print("DIAGNOSTIC: About to call engine.load() with custom mock response")
    from unittest.mock import patch
    mock_response = AsyncMock()
    mock_response.has = True
    mock_response.text = sample_html
    mock_response.__bool__.return_value = True
    mock_instance = mock_safe_request.return_value
    mock_instance.user_agent = lambda *args, **kwargs: None
    mock_instance.request = AsyncMock(return_value=mock_response)
    result = await engine.load()
    print(f"DIAGNOSTIC: engine.load() returned: {result}")
    assert result is not None
    print(f"DIAGNOSTIC: name={getattr(result, 'name', None)}, price={getattr(getattr(result, 'price', None), 'price', None)}, currency={getattr(getattr(result, 'price', None), 'currency', None)}, image={getattr(result, 'image', None)}, status={getattr(result, 'status', None)}")
    assert getattr(result, 'name', None) == "Another Product"
    assert getattr(getattr(result, 'price', None), 'price', None) == 0.0
    assert getattr(getattr(result, 'price', None), 'currency', None) == ""
    status = getattr(result, 'status', None)
    assert status is not None
    assert status.value == ItemStatus.INACTIVE.value

@pytest.mark.asyncio
@patch("custom_components.price_tracker.services.buywisely.engine.SafeRequest")
async def test_get_product_details_multiple_prices(mock_safe_request):
    # ...existing code...
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
    mock_response = AsyncMock()
    mock_response.has = True
    mock_response.text = sample_html
    mock_response.__bool__.return_value = True
    print(f"DIAGNOSTIC: mock_response.has={getattr(mock_response, 'has', None)}")
    print(f"DIAGNOSTIC: mock_response.text={getattr(mock_response, 'text', None)}")
    print(f"DIAGNOSTIC: mock_response.__bool__={mock_response.__bool__()}")
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

    class MockSafeRequest:
        def user_agent(self, *args, **kwargs):
            pass
        async def request(self, *args, **kwargs):
            return mock_response
    engine = BuyWiselyEngine(item_url="http://example.com/product/multiple-prices", request_cls=MockSafeRequest)
    
    print("DIAGNOSTIC: About to call engine.load() with custom mock response")
    from unittest.mock import patch
    mock_response = AsyncMock()
    mock_response.has = True
    mock_response.text = sample_html
    mock_response.__bool__.return_value = True
    mock_instance = mock_safe_request.return_value
    mock_instance.user_agent = lambda *args, **kwargs: None
    mock_instance.request = AsyncMock(return_value=mock_response)
    result = await engine.load()
    print(f"DIAGNOSTIC: engine.load() returned: {result}")
    assert result is not None
    print(f"DIAGNOSTIC: name={getattr(result, 'name', None)}, price={getattr(getattr(result, 'price', None), 'price', None)}, currency={getattr(getattr(result, 'price', None), 'currency', None)}, image={getattr(result, 'image', None)}, status={getattr(result, 'status', None)}")
    assert getattr(result, 'name', None) == "Product with Multiple Prices"
    assert getattr(getattr(result, 'price', None), 'price', None) == 99.50
    assert getattr(getattr(result, 'price', None), 'currency', None) == "AUD"
    assert getattr(result, 'image', None) == "http://example.com/multiple_prices.jpg"
    status = getattr(result, 'status', None)
    assert status is not None
    assert status.value == ItemStatus.ACTIVE.value

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
