import os
import pytest
from unittest.mock import AsyncMock, patch
from services.buywisely.engine import BuyWiselyEngine
from datas.item import ItemStatus

@pytest.mark.asyncio
@patch("custom_components.price_tracker.services.buywisely.engine.SafeRequest")
async def test_real_fetched_html_product_parsing(mock_safe_request):
    # Path to the real fetched HTML file
    html_path = os.path.join(os.path.dirname(__file__), "buywisely_retriever_test", "buywisely_fetched.html")
    assert os.path.exists(html_path), f"Test HTML file not found: {html_path}"
    with open(html_path, "r", encoding="utf-8") as f:
        sample_html = f.read()

    mock_response = AsyncMock()
    mock_response.has = True
    mock_response.text = sample_html
    mock_response.__bool__.return_value = True

    class MockSafeRequest:
        def user_agent(self, *args, **kwargs):
            pass
        async def request(self, *args, **kwargs):
            return mock_response

    engine = BuyWiselyEngine(item_url="https://www.buywisely.com.au/product/motorola-moto-g75-5g-256gb-grey-with-buds", request_cls=MockSafeRequest)
    mock_instance = mock_safe_request.return_value
    mock_instance.user_agent = lambda *args, **kwargs: None
    mock_instance.request = AsyncMock(return_value=mock_response)
    result = await engine.load()
    print(f"DIAGNOSTIC: engine.load() returned: {result}")
    assert result is not None, "BuyWiselyEngine.load() returned None for real fetched HTML test."
    print(f"DIAGNOSTIC: name={getattr(result, 'name', None)}, price={getattr(getattr(result, 'price', None), 'price', None)}, currency={getattr(getattr(result, 'price'), 'currency', None)}, image={getattr(result, 'image', None)}, status={getattr(result, 'status', None)}")
    status = getattr(result, 'status', None)
    assert status is not None
    assert status.value == ItemStatus.ACTIVE.value
