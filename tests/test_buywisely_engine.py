import sys
import os
import pytest
from unittest.mock import AsyncMock, patch
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from custom_components.price_tracker.services.buywisely.engine import BuyWiselyEngine


from custom_components.price_tracker.datas.item import ItemStatus
from custom_components.price_tracker.services.buywisely.parser import parse_product

@pytest.mark.asyncio
@patch("custom_components.price_tracker.services.buywisely.engine.SafeRequest")
async def test_real_html_product_parsing(mock_safe_request):
    sample_html = """
    <html>
    <body>
        <script id="__NEXT_DATA__" type="application/json">
        {{"props":{{"pageProps":{{"product":{{"title":"Sony - WH-1000XM4 Wireless Noise Cancelling Headphones - Black","slug":"sony-wh-1000xm4-wireless-noise-cancelling-headphones-black-1","availability":"In Stock","offers":[{{"base_price":348.00}}],"image":"https://buywisely.com.au/product/sony-wh-1000xm4-wireless-noise-cancelling-headphones-black-1"}}}}}}}}
        </script>
    </body>
    </html>
    """
    mock_response = AsyncMock()
    mock_response.has = True
    mock_response.text = sample_html
    mock_response.__bool__.return_value = True

    class MockSafeRequest:
        def user_agent(self, *args, **kwargs):
            pass
        async def request(self, *args, **kwargs):
            return mock_response
    engine = BuyWiselyEngine(item_url="https://buywisely.com.au/product/sony-wh-1000xm4-wireless-noise-cancelling-headphones-black-1?id=12345", request_cls=MockSafeRequest)
    mock_response = AsyncMock()
    mock_response.has = True
    mock_response.text = sample_html
    mock_response.__bool__.return_value = True
    mock_instance = mock_safe_request.return_value
    mock_instance.user_agent = lambda *args, **kwargs: None
    mock_instance.request = AsyncMock(return_value=mock_response)
    result = await engine.load()
    assert result is not None
    assert getattr(result, 'name', None) == "Sony - WH-1000XM4 Wireless Noise Cancelling Headphones - Black"
    assert result.price.price == 348.00
    assert getattr(getattr(result, 'price', None), 'currency', None) == "AUD"
    assert getattr(result, 'image', None) == "https://buywisely.com.au/product/sony-wh-1000xm4-wireless-noise-cancelling-headphones-black-1"
    status = getattr(result, 'status', None)
    assert status is not None
    assert status.value == ItemStatus.ACTIVE.value
@pytest.mark.asyncio
@patch("custom_components.price_tracker.services.buywisely.engine.SafeRequest")
async def test_get_product_details_success(mock_safe_request):
    sample_html = """
    <html>
    <body>
        <script id="__NEXT_DATA__" type="application/json">
        {{"props":{{"pageProps":{{"product":{{"title":"Test Product Title","slug":"test-product","availability":"In Stock","offers":[{{"base_price":123.45}}],"image":"http://example.com/test_image.jpg"}}}}}}}}
        </script>
    </body>
    </html>
    """
    mock_response = AsyncMock()
    mock_response.has = True
    mock_response.text = sample_html
    mock_response.__bool__.return_value = True

    class MockSafeRequest:
        def user_agent(self, *args, **kwargs):
            pass
        async def request(self, *args, **kwargs):
            return mock_response
    engine = BuyWiselyEngine(item_url="http://example.com/product/test-product", request_cls=MockSafeRequest)
    
    mock_response = AsyncMock()
    mock_response.has = True
    mock_response.text = sample_html
    mock_response.__bool__.return_value = True
    mock_instance = mock_safe_request.return_value
    mock_instance.user_agent = lambda *args, **kwargs: None
    mock_instance.request = AsyncMock(return_value=mock_response)
    result = await engine.load()
    assert result is not None
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
    sample_html = """
    <html>
    <body>
        <script id="__NEXT_DATA__" type="application/json">
        {{"props":{{"pageProps":{{"product":{{"title":"Another Product","slug":"another-product","availability":"Out of Stock","offers":[],"image":"http://example.com/another_image.jpg"}}}}}}}}
        </script>
    </body>
    </html>
    """
    mock_response = AsyncMock()
    mock_response.has = True
    mock_response.text = sample_html
    mock_response.__bool__.return_value = True

    class MockSafeRequest:
        def user_agent(self, *args, **kwargs):
            pass
        async def request(self, *args, **kwargs):
            return mock_response
    engine = BuyWiselyEngine(item_url="http://example.com/product/another-product", request_cls=MockSafeRequest)
    
    mock_response = AsyncMock()
    mock_response.has = True
    mock_response.text = sample_html
    mock_response.__bool__.return_value = True
    mock_instance = mock_safe_request.return_value
    mock_instance.user_agent = lambda *args, **kwargs: None
    mock_instance.request = AsyncMock(return_value=mock_response)
    result = await engine.load()
    assert result is not None
    assert getattr(result, 'name', None) == "Another Product"
    assert getattr(getattr(result, 'price', None), 'price', None) == 0.0
    assert getattr(getattr(result, 'price', None), 'currency', None) == ""
    status = getattr(result, 'status', None)
    assert status is not None
    assert status.value == ItemStatus.INACTIVE.value

@pytest.mark.asyncio
@patch("custom_components.price_tracker.services.buywisely.engine.SafeRequest")
async def test_get_product_details_multiple_prices(mock_safe_request):
    sample_html = """
    <html>
    <body>
        <script id="__NEXT_DATA__" type="application/json">
        {{"props":{{"pageProps":{{"product":{{"title":"Product with Multiple Prices","slug":"multiple-prices","availability":"In Stock","offers":[{{"base_price":100.00}},{{"base_price":99.50}}],"image":"http://example.com/multiple_prices.jpg"}}}}}}}}
        </script>
    </body>
    </html>
    """
    mock_response = AsyncMock()
    mock_response.has = True
    mock_response.text = sample_html
    mock_response.__bool__.return_value = True

    class MockSafeRequest:
        def user_agent(self, *args, **kwargs):
            pass
        async def request(self, *args, **kwargs):
            return mock_response
    engine = BuyWiselyEngine(item_url="http://example.com/product/multiple-prices", request_cls=MockSafeRequest)
    
    mock_response = AsyncMock()
    mock_response.has = True
    mock_response.text = sample_html
    mock_response.__bool__.return_value = True
    mock_instance = mock_safe_request.return_value
    mock_instance.user_agent = lambda *args, **kwargs: None
    mock_instance.request = AsyncMock(return_value=mock_response)
    result = await engine.load()
    assert result is not None
    assert getattr(result, 'name', None) == "Product with Multiple Prices"
    assert getattr(getattr(result, 'price', None), 'price', None) == 99.50
    assert getattr(getattr(result, 'price', None), 'currency', None) == "AUD"
    assert getattr(result, 'image', None) == "http://example.com/multiple_prices.jpg"
    status = getattr(result, 'status', None)
    assert status is not None
    assert status.value == ItemStatus.ACTIVE.value

@pytest.mark.asyncio
@patch("custom_components.price_tracker.services.buywisely.engine.SafeRequest")
async def test_lowest_price_selection(mock_safe_request):
    sample_html = """
    <html>
    <body>
        <script id="__NEXT_DATA__" type="application/json">
        {{"props":{{"pageProps":{{"product":{{"title":"Product with Multiple Prices","slug":"multiple-prices","availability":"In Stock","offers":[
            {{"base_price":100.00, "currency": "AUD"}},
            {{"base_price":99.50, "currency": "AUD"}},
            {{"base_price":10.00, "currency": "AUD"}},
            {{"base_price":150.00, "currency": "AUD"}},
            {{"base_price":75.00, "currency": "AUD"}},
            {{"base_price":200.00, "currency": "AUD"}},
            {{"base_price":5.00, "currency": "AUD"}},
            {{"base_price":120.00, "currency": "AUD"}},
            {{"base_price":80.00, "currency": "AUD"}},
            {{"base_price":110.00, "currency": "AUD"}}
        ]}}}}}}}}
        </script>
    </body>
    </html>
    """
    mock_response = AsyncMock()
    mock_response.has = True
    mock_response.text = sample_html
    mock_response.__bool__.return_value = True
    mock_instance = mock_safe_request.return_value
    mock_instance.user_agent = lambda *args, **kwargs: None
    mock_instance.request = AsyncMock(return_value=mock_response)

    class MockSafeRequest:
        def user_agent(self, *args, **kwargs):
            pass
        async def request(self, *args, **kwargs):
            return mock_response
    engine = BuyWiselyEngine(item_url="http://example.com/product/multiple-prices", request_cls=MockSafeRequest)
    result = await engine.load()

    assert result is not None
    assert result.price.price == 5.00
    assert result.price.currency == "AUD"
    assert result.name == "Product with Multiple Prices"
    assert result.status.value == ItemStatus.ACTIVE.value

@pytest.mark.asyncio
@patch("custom_components.price_tracker.services.buywisely.engine.SafeRequest")
async def test_product_url_extraction_from_next_data(mock_safe_request):
    sample_html = """
    <html>
    <body>
        <script id="__NEXT_DATA__" type="application/json">
        {{"props":{{"pageProps":{{"product":{{"title":"Test Product Title","availability":"In Stock","slug":"test-product-slug-123","offers":[{{"base_price":123.45}}]}}}}}}}}
        </script>
    </body>
    </html>
    """
    mock_response = AsyncMock()
    mock_response.has = True
    mock_response.text = sample_html
    mock_response.__bool__.return_value = True
    mock_instance = mock_safe_request.return_value
    mock_instance.user_agent = lambda *args, **kwargs: None
    mock_instance.request = AsyncMock(return_value=mock_response)

    class MockSafeRequest:
        def user_agent(self, *args, **kwargs):
            pass
        async def request(self, *args, **kwargs):
            return mock_response
    engine = BuyWiselyEngine(item_url="http://example.com/product/test-product", request_cls=MockSafeRequest)
    result = await engine.load()

    assert result is not None
    assert result.url == "https://www.buywisely.com.au/product/test-product-slug-123"
    assert result.name == "Test Product Title"
    assert result.price.price == 123.45
    assert result.status.value == ItemStatus.ACTIVE.value

@pytest.mark.asyncio
@patch("custom_components.price_tracker.services.buywisely.engine.SafeRequest")
async def test_product_url_fallback_to_item_url_when_no_slug(mock_safe_request):
    test_item_url = "http://example.com/product/original-product-url"
    sample_html = """
    <html>
    <body>
        <script id="__NEXT_DATA__" type="application/json">
        {{"props":{{"pageProps":{{"product":{{"title":"Test Product Title","availability":"In Stock","offers":[{{"base_price":123.45}}]}}}}}}}}
        </script>
    </body>
    </html>
    """
    mock_response = AsyncMock()
    mock_response.has = True
    mock_response.text = sample_html
    mock_response.__bool__.return_value = True
    mock_instance = mock_safe_request.return_value
    mock_instance.user_agent = lambda *args, **kwargs: None
    mock_instance.request = AsyncMock(return_value=mock_response)

    class MockSafeRequest:
        def user_agent(self, *args, **kwargs):
            pass
        async def request(self, *args, **kwargs):
            return mock_response
    engine = BuyWiselyEngine(item_url=test_item_url, request_cls=MockSafeRequest)
    result = await engine.load()

    assert result is not None
    assert result.url == test_item_url
    assert result.name == "Test Product Title"
    assert result.price.price == 123.45
    assert result.status.value == ItemStatus.ACTIVE.value

# Test cases for parse_product directly
def test_parse_product_basic():
    html = """
    <html>
    <body>
        <script id="__NEXT_DATA__" type="application/json">
        {{"props":{{"pageProps":{{"product":{{"title":"Direct Parse Test","slug":"direct-parse-test","availability":"In Stock","offers":[{{"base_price":50.00}}],"image":"http://example.com/direct_parse.jpg"}}}}}}}}
        </script>
    </body>
    </html>
    """
    result = parse_product(html)
    assert result.name == "Direct Parse Test"
    assert result.price.price == 50.00
    assert result.image == "http://example.com/direct_parse.jpg"
    assert result.price.currency == "AUD"
    assert result.status == ItemStatus.ACTIVE

def test_parse_product_euro_currency():
    html = """
    <html>
    <body>
        <script id="__NEXT_DATA__" type="application/json">
        {{"props":{{"pageProps":{{"product":{{"title":"Euro Product","slug":"euro-product","availability":"In Stock","offers":[{{"base_price":25.99,"currency":"EUR"}}],"image":"http://example.com/euro_product.jpg"}}}}}}}}
        </script>
    </body>
    </html>
    """
    result = parse_product(html)
    assert result.price.price == 25.99
    assert result.price.currency == "EUR"

def test_parse_product_no_image():
    html = """
    <html>
    <body>
        <script id="__NEXT_DATA__" type="application/json">
        {{"props":{{"pageProps":{{"product":{{"title":"No Image Product","slug":"no-image-product","availability":"In Stock","offers":[{{"base_price":75.00}}]}}}}}}}}
        </script>
    </body>
    </html>
    """
    result = parse_product(html)
    assert result.image == ""

def test_html_extractor_import_and_basic_call():
    from custom_components.price_tracker.services.buywisely.html_extractor import extract_product_data_from_html
    html_content = "<html><body></body></html>"
    result = extract_product_data_from_html(html_content)
    assert isinstance(result, dict)
    assert "title" not in result
    assert "price" not in result
    assert "url" not in result

@pytest.mark.asyncio
@patch("custom_components.price_tracker.services.buywisely.engine.SafeRequest")
async def test_html_extractor_finds_next_data_script(mock_safe_request):

    class MockSafeRequest:
        def user_agent(self, *args, **kwargs):
            pass
        async def request(self, *args, **kwargs):
            return mock_response

    sample_html = """
    <html>
    <body>
        <script id="__NEXT_DATA__" type="application/json">
        {{"props":{{"pageProps":{{"product":{{"availability":"In Stock","slug":"test-slug"}}}}}}}}
        </script>
    </body>
    </html>
    """
    # Mock the SafeRequest response
    mock_response = AsyncMock()
    mock_response.has = True
    mock_response.text = sample_html
    mock_response.__bool__.return_value = True
    mock_instance = mock_safe_request.return_value
    mock_instance.user_agent = lambda *args, **kwargs: None
    mock_instance.request = AsyncMock(return_value=mock_response)

    # Call the engine's load method to trigger html_extractor
    engine = BuyWiselyEngine(item_url="http://example.com/product/test-product", request_cls=MockSafeRequest)
    result = await engine.load()

    # Assert that the URL was correctly extracted from __NEXT_DATA__
    assert result is not None
    assert result.url == "https://www.buywisely.com.au/product/test-slug"
