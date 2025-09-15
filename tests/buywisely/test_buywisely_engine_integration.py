import sys
import os
import pytest
from unittest.mock import AsyncMock, patch
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from custom_components.price_tracker.services.buywisely.engine import BuyWiselyEngine

@pytest.mark.asyncio
@patch("custom_components.price_tracker.services.buywisely.engine.SafeRequest")
async def test_real_html_hydration_extraction(mock_safe_request):
    """
    Integration test: Use real BuyWisely HTML fixture to validate Next.js hydration extraction logic.
    """
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "real_buywisely_fetched.html")
    with open(fixture_path, encoding="utf-8") as f:
        real_html = f.read()
    mock_response = AsyncMock()
    mock_response.has = True
    mock_response.text = real_html
    mock_response.__bool__.return_value = True

    class MockSafeRequest:
        def user_agent(self, *args, **kwargs):
            pass
        async def request(self, *args, **kwargs):
            return mock_response

    engine = BuyWiselyEngine(item_url="https://buywisely.com.au/product/real-fixture-test", request_cls=MockSafeRequest)
    mock_instance = mock_safe_request.return_value
    mock_instance.user_agent = lambda *args, **kwargs: None
    mock_instance.request = AsyncMock(return_value=mock_response)
    print("[DIAG] Using real HTML fixture for hydration extraction test.")
    result = await engine.load()
    print("[DIAG] Extraction result from real HTML:", result)
    # Assert that at least a name/title and offers are present (real-world data)
    assert result is not None, "Expected result, got None"
    assert getattr(result, 'name', None), "Expected a product name from real HTML"
    assert getattr(result, 'price', None) is not None, "Expected a price object from real HTML"
    assert getattr(getattr(result, 'price', None), 'price', None) is not None, "Expected a price value from real HTML"
    assert getattr(result, 'image', None) is not None, "Expected an image URL from real HTML"
    # Optionally, print more fields for diagnostics
    print("[DIAG] Name:", getattr(result, 'name', None))
    print("[DIAG] Price:", getattr(getattr(result, 'price', None), 'price', None))
    print("[DIAG] Image:", getattr(result, 'image', None))
    print("[DIAG] Offers:", getattr(result, 'offers', None))
