import sys
import pytest
from unittest.mock import patch
sys.path.insert(0, '/mnt/e/Source/Repos/homeassistant/custom/price_tracker/hs-price-tracker')

@pytest.mark.asyncio
@patch("custom_components.price_tracker.services.buywisely.engine.SafeRequest")
async def test_real_html_product_parsing(mock_safe_request):
    # ...existing code...
    pass
