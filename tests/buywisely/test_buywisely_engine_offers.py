import pytest
from unittest.mock import AsyncMock, patch
from custom_components.price_tracker.services.buywisely.engine import BuyWiselyEngine
from custom_components.price_tracker.datas.item import ItemStatus

@pytest.mark.asyncio
@patch("custom_components.price_tracker.services.buywisely.engine.SafeRequest")
async def test_get_product_details_success(mock_safe_request):
    sample_html = (
        '<html><body><script id="__NEXT_DATA__" type="application/json">'
        '{"props":{"pageProps":{"product":{"title":"Test Product Title","slug":"test-product","availability":"In Stock","offers":[{"base_price":123.45,"currency":"AUD"}],"image":"http://example.com/test_image.jpg"}}}}'
        '</script></body></html>'
    )
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
    print("[DIAG] HTML passed to parser:", sample_html)
    result = await engine.load()
    print("[DIAG] result:", result)
    assert result is not None, "Expected result, got None"
    assert getattr(result, 'name', None) == "Test Product Title", f"Name mismatch: {getattr(result, 'name', None)}"
    assert getattr(getattr(result, 'price', None), 'price', None) == 123.45, f"Price mismatch: {getattr(getattr(result, 'price', None), 'price', None)}"
    assert getattr(getattr(result, 'price', None), 'currency', None) == "AUD", f"Currency mismatch: {getattr(getattr(result, 'price', None), 'currency', None)}"
    assert getattr(result, 'image', None) == "http://example.com/test_image.jpg", f"Image mismatch: {getattr(result, 'image', None)}"
    status = getattr(result, 'status', None)
    assert status is not None, "Status missing"
    assert status.value == ItemStatus.ACTIVE.value, f"Status value mismatch: {status.value}"

@pytest.mark.asyncio
@patch("custom_components.price_tracker.services.buywisely.engine.SafeRequest")
async def test_get_product_details_no_price(mock_safe_request):
    sample_html = (
        '<html><body><script id="__NEXT_DATA__" type="application/json">'
        '{"props":{"pageProps":{"product":{"title":"Another Product","slug":"another-product","availability":"Out of Stock","offers":[],"image":"http://example.com/another_image.jpg"}}}}'
        '</script></body></html>'
    )
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
    print("[DIAG] HTML passed to parser:", sample_html)
    result = await engine.load()
    print("[DIAG] result:", result)
    assert result is not None, "Expected result, got None"
    assert getattr(result, 'name', None) == "Another Product", f"Name mismatch: {getattr(result, 'name', None)}"
    assert getattr(getattr(result, 'price', None), 'price', None) == 0.0, f"Price mismatch: {getattr(getattr(result, 'price', None), 'price', None)}"
    assert getattr(getattr(result, 'price', None), 'currency', None) == "", f"Currency mismatch: {getattr(getattr(result, 'price', None), 'currency', None)}"
    status = getattr(result, 'status', None)
    assert status is not None, "Status missing"
    assert status.value == ItemStatus.INACTIVE.value, f"Status value mismatch: {status.value}"

@pytest.mark.asyncio
@patch("custom_components.price_tracker.services.buywisely.engine.SafeRequest")
async def test_get_product_details_multiple_prices(mock_safe_request):
    sample_html = (
        '<html><body><script id="__NEXT_DATA__" type="application/json">'
        '{"props":{"pageProps":{"product":{"title":"Product with Multiple Prices","slug":"multiple-prices","availability":"In Stock","offers":[{"base_price":100.00,"currency":"AUD"},{"base_price":99.50,"currency":"AUD"}],"image":"http://example.com/multiple_prices.jpg"}}}}'
        '</script></body></html>'
    )
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
    print("[DIAG] HTML passed to parser:", sample_html)
    result = await engine.load()
    print("[DIAG] result:", result)
    assert result is not None, "Expected result, got None"
    assert getattr(result, 'name', None) == "Product with Multiple Prices", f"Name mismatch: {getattr(result, 'name', None)}"
    assert getattr(getattr(result, 'price', None), 'price', None) == 99.50, f"Price mismatch: {getattr(getattr(result, 'price', None), 'price', None)}"
    assert getattr(getattr(result, 'price', None), 'currency', None) == "AUD", f"Currency mismatch: {getattr(getattr(result, 'price', None), 'currency', None)}"
    assert getattr(result, 'image', None) == "http://example.com/multiple_prices.jpg", f"Image mismatch: {getattr(result, 'image', None)}"
    status = getattr(result, 'status', None)
    assert status is not None, "Status missing"
    assert status.value == ItemStatus.ACTIVE.value, f"Status value mismatch: {status.value}"

@pytest.mark.asyncio
@patch("custom_components.price_tracker.services.buywisely.engine.SafeRequest")
async def test_lowest_price_selection(mock_safe_request):
    sample_html = '<html><body><script id="__NEXT_DATA__" type="application/json">{"props":{"pageProps":{"product":{"title":"Product with Multiple Prices","slug":"multiple-prices","availability":"In Stock","offers":[{"base_price":100.00,"currency":"AUD"},{"base_price":99.50,"currency":"AUD"},{"base_price":10.00,"currency":"AUD"},{"base_price":150.00,"currency":"AUD"},{"base_price":75.00,"currency":"AUD"},{"base_price":200.00,"currency":"AUD"},{"base_price":5.00,"currency":"AUD"},{"base_price":120.00,"currency":"AUD"},{"base_price":80.00,"currency":"AUD"},{"base_price":110.00,"currency":"AUD"}],"image":"http://example.com/multiple_prices.jpg"}}}}</script></body></html>'
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
    print("[DIAG] HTML passed to parser:", sample_html)
    result = await engine.load()

    print("[DIAG] result:", result)
    assert result is not None, "Expected result, got None"
    assert getattr(getattr(result, 'price', None), 'price', None) == 5.00, f"Lowest price mismatch: {getattr(getattr(result, 'price', None), 'price', None)}"
    assert getattr(getattr(result, 'price', None), 'currency', None) == "AUD", f"Currency mismatch: {getattr(getattr(result, 'price', None), 'currency', None)}"
    assert getattr(result, 'name', None) == "Product with Multiple Prices", f"Name mismatch: {getattr(result, 'name', None)}"
    status = getattr(result, 'status', None)
    assert status is not None, "Status missing"
    assert getattr(status, 'value', None) == ItemStatus.ACTIVE.value, f"Status value mismatch: {getattr(status, 'value', None)}"
