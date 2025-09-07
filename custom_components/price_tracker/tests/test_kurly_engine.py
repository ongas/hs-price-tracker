import pytest
import sys
import os
# Add both possible package roots to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../custom_components/price_tracker/custom_components/price_tracker')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../custom_components/price_tracker')))
from custom_components.price_tracker.services.kurly.engine import KurlyEngine


@pytest.hookimpl(trylast=True)
@pytest.mark.asyncio
async def test_kurly_parse_1():
    engine = KurlyEngine(
        item_url="https://www.kurly.com/goods/5159822",
    )
    result = await engine.load()
    assert result is not None
    assert result.name is not None
