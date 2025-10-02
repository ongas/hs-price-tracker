import json
import pytest
from unittest.mock import AsyncMock, patch
from bs4 import BeautifulSoup
from custom_components.price_tracker.services.buywisely.engine import BuyWiselyEngine
from custom_components.price_tracker.datas.item import ItemStatus


@pytest.mark.asyncio
@patch(
    "custom_components.price_tracker.services.buywisely.data_transformer._fetch_and_parse_seller_price"
)
@patch("custom_components.price_tracker.utilities.safe_request.SafeRequest")
async def test_price_validation_loop_selects_matching_offer(
    mock_safe_request, mock_fetch_seller_price
):
    # Simulate three offers, only the second matches seller page price
    offers = [
        {
            "base_price": 100.00,
            "currency": "AUD",
            "seller_product_url": "http://example.com/seller1",
            "created_at": "$D2025-09-28T22:34:51.002Z",
            "seller": {"shopback": None, "cashrewards": None},
        },
        {
            "base_price": 99.50,
            "currency": "AUD",
            "seller_product_url": "http://example.com/seller2",
            "created_at": "$D2025-09-28T22:34:51.002Z",
            "seller": {"shopback": None, "cashrewards": None},
        },
        {
            "base_price": 120.00,
            "currency": "AUD",
            "seller_product_url": "http://example.com/seller3",
            "created_at": "$D2025-09-28T22:34:51.002Z",
            "seller": {"shopback": None, "cashrewards": None},
        },
    ]
    sample_html = (
        '<html><body><script id="__NEXT_DATA__" type="application/json">'
        f'{{"props":{{"pageProps":{{"product":{{"title":"Product","slug":"product","availability":"In Stock","offers":{json.dumps(offers)},"image":"http://example.com/image.jpg"}}}}}}}}'
        "</script></body></html>"
    )
    # Seller page HTMLs: only seller2 matches the BuyWisely price
    seller_htmls = {
        "http://example.com/seller1": "<html><body><span>$101.00</span></body></html>",
        "http://example.com/seller2": "<html><body><span>$99.50</span></body></html>",
        "http://example.com/seller3": "<html><body><span>$121.00</span></body></html>",
    }
    mock_instance = mock_safe_request.return_value
    mock_instance.user_agent = AsyncMock()
    mock_instance.request = AsyncMock(
        return_value=AsyncMock(has=True, text=sample_html, __bool__=lambda: True)
    )

    def fetch_seller_price_side_effect(url, expected_price):
        for offer_url, html in seller_htmls.items():
            if url == offer_url:
                soup = BeautifulSoup(html, "html.parser")
                price_text = soup.find("span").get_text(strip=True).replace("$", "")
                return float(price_text)
        return None

    mock_fetch_seller_price.side_effect = fetch_seller_price_side_effect

    engine = BuyWiselyEngine(
        item_url="https://www.buywisely.com.au/product/product",
        request_cls=mock_safe_request,
    )
    result = await engine.load()
    # Should select the second offer (99.50) as it matches seller page
    assert (
        getattr(getattr(result, "price", None), "price", None) == 99.5
    ), "Did not select the correct matching offer price"
    assert (
        getattr(result, "status", None).value == ItemStatus.ACTIVE.value
    ), "Status should be ACTIVE for matching offer"


@pytest.mark.asyncio
@patch(
    "custom_components.price_tracker.services.buywisely.data_transformer._fetch_and_parse_seller_price"
)
@patch("custom_components.price_tracker.utilities.safe_request.SafeRequest")
async def test_price_validation_loop_handles_no_matching_offer(
    mock_safe_request, mock_fetch_seller_price
):
    # All seller pages have mismatched prices
    offers = [
        {
            "base_price": 100.00,
            "currency": "AUD",
            "seller_product_url": "http://example.com/seller1",
            "created_at": "$D2025-09-28T22:34:51.002Z",
            "seller": {"shopback": None, "cashrewards": None},
        },
        {
            "base_price": 99.50,
            "currency": "AUD",
            "seller_product_url": "http://example.com/seller2",
            "created_at": "$D2025-09-28T22:34:51.002Z",
            "seller": {"shopback": None, "cashrewards": None},
        },
    ]
    sample_html = (
        '<html><body><script id="__NEXT_DATA__" type="application/json">'
        f'{{"props":{{"pageProps":{{"product":{{"title":"Product","slug":"product","availability":"In Stock","offers":{json.dumps(offers)},"image":"http://example.com/image.jpg"}}}}}}}}'
        "</script></body></html>"
    )
    seller_htmls = {
        "http://example.com/seller1": "<html><body><span>$101.00</span></body></html>",
        "http://example.com/seller2": "<html><body><span>$98.00</span></body></html>",
    }
    mock_instance = mock_safe_request.return_value
    mock_instance.user_agent = AsyncMock()
    mock_instance.request = AsyncMock(
        return_value=AsyncMock(has=True, text=sample_html, __bool__=lambda: True)
    )

    def fetch_seller_price_side_effect(url, expected_price):
        for offer_url, html in seller_htmls.items():
            if url == offer_url:
                soup = BeautifulSoup(html, "html.parser")
                price_text = soup.find("span").get_text(strip=True).replace("$", "")
                return float(price_text)
        return None

    mock_fetch_seller_price.side_effect = fetch_seller_price_side_effect

    engine = BuyWiselyEngine(
        item_url="https://www.buywisely.com.au/product/product",
        request_cls=mock_safe_request,
    )
    result = await engine.load()
    # Should mark as price mismatch (status or attribute)
    assert (
        getattr(result, "status", None).value == ItemStatus.PRICE_MISMATCH.value
    ), "Status should be PRICE_MISMATCH when no offer matches seller page price"
