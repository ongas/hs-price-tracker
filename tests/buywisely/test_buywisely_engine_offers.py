import pytest
from unittest.mock import AsyncMock, patch
from custom_components.price_tracker.services.buywisely.engine import BuyWiselyEngine
from custom_components.price_tracker.datas.item import ItemStatus

@pytest.mark.asyncio
@patch("custom_components.price_tracker.services.buywisely.engine.SafeRequest")
async def test_get_product_details_success(mock_safe_request):
    sample_html = (
        '<html><body><script id="__NEXT_DATA__" type="application/json">'
        '{"props":{"pageProps":{"product":{"title":"Test Product Title","slug":"test-product","availability":"In Stock","offers":[{"base_price":123.45,"currency":"AUD","seller_product_url":"http://example.com/seller_product_url"}],"image":"http://example.com/test_image.jpg"}}}}'
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
async def test_get_product_details_multiple_prices(mock_safe_request):
    sample_html = (
        '<html><body><script id="__NEXT_DATA__" type="application/json">'
        '{"props":{"pageProps":{"product":{"title":"Product with Multiple Prices","slug":"multiple-prices","availability":"In Stock","offers":[{"base_price":100.00,"currency":"AUD","seller_product_url":"http://example.com/seller_product_url_1"},{"base_price":99.50,"currency":"AUD","seller_product_url":"http://example.com/seller_product_url_2"}],"image":"http://example.com/multiple_prices.jpg"}}}}'
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
async def test_price_must_be_greater_than_zero(mock_safe_request):
    # Test case 1: Valid product with non-zero price
    sample_html_valid_price = (
        '<html><body><script id="__NEXT_DATA__" type="application/json">'
        '{"props":{"pageProps":{"product":{"title":"Valid Product","slug":"valid-product","availability":"In Stock","offers":[{"base_price":10.00,"currency":"AUD","seller_product_url":"http://example.com/valid_offer"}],"image":"http://example.com/valid_image.jpg"}}}}'
        '</script></body></html>'
    )
    mock_response_valid = AsyncMock()
    mock_response_valid.has = True
    mock_response_valid.text = sample_html_valid_price
    mock_response_valid.__bool__.return_value = True

    class MockSafeRequestValid:
        def user_agent(self, *args, **kwargs):
            pass
        async def request(self, *args, **kwargs):
            return mock_response_valid
    engine_valid = BuyWiselyEngine(item_url="http://example.com/product/valid-product", request_cls=MockSafeRequestValid)
    result_valid = await engine_valid.load()
    assert result_valid is not None
    assert getattr(getattr(result_valid, 'price', None), 'price', None) > 0.0, "Price should be greater than 0 for a valid product"

    # Test case 2: Product with zero price - should raise an exception
    sample_html_zero_price = (
        '<html><body><script id="__NEXT_DATA__" type="application/json">'
        '{"props":{"pageProps":{"product":{"title":"Zero Price Product","slug":"zero-price-product","availability":"In Stock","offers":[{"base_price":0.00,"currency":"AUD","seller_product_url":"http://example.com/zero_offer"}],"image":"http://example.com/zero_image.jpg"}}}}'
        '</script></body></html>'
    )
    mock_response_zero = AsyncMock()
    mock_response_zero.has = True
    mock_response_zero.text = sample_html_zero_price
    mock_response_zero.__bool__.return_value = True

    class MockSafeRequestZero:
        def user_agent(self, *args, **kwargs):
            pass
        async def request(self, *args, **kwargs):
            return mock_response_zero
    engine_zero = BuyWiselyEngine(item_url="http://example.com/product/zero-price-product", request_cls=MockSafeRequestZero)
    
    # Expect an exception to be raised when loading a product with a zero price
    with pytest.raises(ValueError, match="Extracted price cannot be zero or less."):
        await engine_zero.load()

    # Test case 3: Product with missing price - should raise an exception
    sample_html_missing_price = (
        '<html><body><script id="__NEXT_DATA__" type="application/json">'
        '{"props":{"pageProps":{"product":{"title":"Missing Price Product","slug":"missing-price-product","availability":"In Stock","offers":[{"currency":"AUD","seller_product_url":"http://example.com/missing_offer"}],"image":"http://example.com/missing_image.jpg"}}}}'
        '</script></body></html>'
    )
    mock_response_missing = AsyncMock()
    mock_response_missing.has = True
    mock_response_missing.text = sample_html_missing_price
    mock_response_missing.__bool__.return_value = True

    class MockSafeRequestMissing:
        def user_agent(self, *args, **kwargs):
            pass
        async def request(self, *args, **kwargs):
            return mock_response_missing
    engine_missing = BuyWiselyEngine(item_url="http://example.com/product/missing-price-product", request_cls=MockSafeRequestMissing)
    
    # Expect an exception to be raised when loading a product with a missing price
    with pytest.raises(ValueError, match="Extracted price cannot be zero or less."):
        await engine_missing.load()

@pytest.mark.asyncio
@patch("custom_components.price_tracker.services.buywisely.engine.SafeRequest")
async def test_lowest_price_selection(mock_safe_request):
    sample_html = '<html><body><script id="__NEXT_DATA__" type="application/json">{"props":{"pageProps":{"product":{"title":"Product with Multiple Prices","slug":"multiple-prices","availability":"In Stock","offers":[{"base_price":100.00,"currency":"AUD","seller_product_url":"http://example.com/offer1"},{"base_price":99.50,"currency":"AUD","seller_product_url":"http://example.com/offer2"},{"base_price":10.00,"currency":"AUD","seller_product_url":"http://example.com/offer3"},{"base_price":150.00,"currency":"AUD","seller_product_url":"http://example.com/offer4"},{"base_price":75.00,"currency":"AUD","seller_product_url":"http://example.com/offer5"},{"base_price":200.00,"currency":"AUD","seller_product_url":"http://example.com/offer6"},{"base_price":5.00,"currency":"AUD","seller_product_url":"http://example.com/offer7"},{"base_price":120.00,"currency":"AUD","seller_product_url":"http://example.com/offer8"},{"base_price":80.00,"currency":"AUD","seller_product_url":"http://example.com/offer9"},{"base_price":110.00,"currency":"AUD","seller_product_url":"http://example.com/offer10"}],"image":"http://example.com/multiple_prices.jpg"}}}}</script></body></html>'
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
