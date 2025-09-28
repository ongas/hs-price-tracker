import pytest
from unittest.mock import AsyncMock, patch
from custom_components.price_tracker.services.buywisely.engine import BuyWiselyEngine
from custom_components.price_tracker.datas.item import ItemStatus

@pytest.mark.asyncio
@patch("custom_components.price_tracker.services.buywisely.engine.SafeRequest")
async def test_iterative_seller_price_validation(mock_safe_request):
    # Simulate three offers, only the second matches seller page price
    offers = [
        {"base_price": 100.00, "currency": "AUD", "seller_product_url": "http://example.com/seller1"},
        {"base_price": 99.50, "currency": "AUD", "seller_product_url": "http://example.com/seller2"},
        {"base_price": 120.00, "currency": "AUD", "seller_product_url": "http://example.com/seller3"},
    ]
    sample_html = (
        '<html><body><script id="__NEXT_DATA__" type="application/json">'
        f'{{"props":{{"pageProps":{{"product":{{"title":"Product","slug":"product","availability":"In Stock","offers":{offers},"image":"http://example.com/image.jpg"}}}}}}}}'
        '</script></body></html>'
    )
    # Seller page HTMLs: only seller2 matches the BuyWisely price
    seller_htmls = {
        "http://example.com/seller1": "<html><body><span>$101.00</span></body></html>",
        "http://example.com/seller2": "<html><body><span>$99.50</span></body></html>",
        "http://example.com/seller3": "<html><body><span>$121.00</span></body></html>",
    }
    # Patch the request to return the product page, then seller pages
    async def request_side_effect(url, *args, **kwargs):
        if url.startswith("https://www.buywisely.com.au/product"):
            mock_response = AsyncMock()
            mock_response.has = True
            mock_response.text = sample_html
            mock_response.__bool__.return_value = True
            return mock_response
        for offer_url, html in seller_htmls.items():
            if url == offer_url:
                mock_response = AsyncMock()
                mock_response.has = True
                mock_response.text = html
                mock_response.__bool__.return_value = True
                return mock_response
        raise Exception("Unknown URL")
    mock_instance = mock_safe_request.return_value
    mock_instance.user_agent = lambda *args, **kwargs: None
    mock_instance.request = AsyncMock(side_effect=request_side_effect)
    engine = BuyWiselyEngine(item_url="https://www.buywisely.com.au/product/product", request_cls=mock_safe_request)
    result = await engine.load()
    # Should select the second offer (99.50) as it matches seller page
    assert getattr(getattr(result, 'price', None), 'price', None) == 99.50, "Did not select the correct matching offer price"
    assert getattr(result, 'status', None).value == ItemStatus.ACTIVE.value, "Status should be ACTIVE for matching offer"

@pytest.mark.asyncio
@patch("custom_components.price_tracker.services.buywisely.engine.SafeRequest")
async def test_no_matching_seller_price_marks_mismatch(mock_safe_request):
    # All seller pages have mismatched prices
    offers = [
        {"base_price": 100.00, "currency": "AUD", "seller_product_url": "http://example.com/seller1"},
        {"base_price": 99.50, "currency": "AUD", "seller_product_url": "http://example.com/seller2"},
    ]
    sample_html = (
        '<html><body><script id="__NEXT_DATA__" type="application/json">'
        f'{{"props":{{"pageProps":{{"product":{{"title":"Product","slug":"product","availability":"In Stock","offers":{offers},"image":"http://example.com/image.jpg"}}}}}}}}'
        '</script></body></html>'
    )
    seller_htmls = {
        "http://example.com/seller1": "<html><body><span>$101.00</span></body></html>",
        "http://example.com/seller2": "<html><body><span>$98.00</span></body></html>",
    }
    async def request_side_effect(url, *args, **kwargs):
        if url.startswith("https://www.buywisely.com.au/product"):
            mock_response = AsyncMock()
            mock_response.has = True
            mock_response.text = sample_html
            mock_response.__bool__.return_value = True
            return mock_response
        for offer_url, html in seller_htmls.items():
            if url == offer_url:
                mock_response = AsyncMock()
                mock_response.has = True
                mock_response.text = html
                mock_response.__bool__.return_value = True
                return mock_response
        raise Exception("Unknown URL")
    mock_instance = mock_safe_request.return_value
    mock_instance.user_agent = lambda *args, **kwargs: None
    mock_instance.request = AsyncMock(side_effect=request_side_effect)
    engine = BuyWiselyEngine(item_url="https://www.buywisely.com.au/product/product", request_cls=mock_safe_request)
    result = await engine.load()
    # Should mark as price mismatch (status or attribute)
    assert getattr(result, 'status', None).value == ItemStatus.PRICE_MISMATCH.value, "Status should be PRICE_MISMATCH when no offer matches seller page price"
