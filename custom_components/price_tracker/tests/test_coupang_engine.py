import pytest
import sys
import os
# Add both possible package roots to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../custom_components/price_tracker/custom_components/price_tracker')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../custom_components/price_tracker')))
from custom_components.price_tracker.services.coupang.engine import CoupangEngine


@pytest.hookimpl(trylast=True)
@pytest.mark.asyncio
async def test_coupang_engine_1():
    engine = CoupangEngine(
        item_url="https://coupang.com/vp/products/6475603839?itemId=14151941530&vendorItemId=81398448965",
    )
    result = await engine.load()

    assert result is not None
    assert result.name is not None


@pytest.hookimpl(trylast=True)
@pytest.mark.asyncio
async def test_coupang_engine_2():
    engine = CoupangEngine(
        item_url="https://www.coupang.com/vp/products/7733420479?vendorItemId=87856547398",
    )
    result = await engine.load()

    assert result is not None
    assert result.name is not None


@pytest.hookimpl(trylast=True)
@pytest.mark.asyncio
async def test_coupang_engine_3():
    engine = CoupangEngine(
        item_url="https://www.coupang.com/vp/products/7632787301?itemId=24262013572&vendorItemId=5133321761"
    )
    result = await engine.load()

    assert result is not None
    assert result.name is not None


@pytest.hookimpl(trylast=True)
@pytest.mark.asyncio
async def test_coupang_engine_4():
    engine = CoupangEngine(
        item_url="https://www.coupang.com/vp/products/8490446925?vendorItemId=91586203772"
    )
    result = await engine.load()

    assert result is not None
    assert result.name is not None


@pytest.hookimpl(trylast=True)
@pytest.mark.asyncio
async def test_coupang_engine_5():
    engine = CoupangEngine(
        item_url="https://www.coupang.com/vp/products/332471584?vendorItemId=86137801306"
    )
    result = await engine.load()

    assert result is not None
    assert result.name is not None


@pytest.hookimpl(trylast=True)
@pytest.mark.asyncio
async def test_coupang_engine_6():
    engine = CoupangEngine(
        item_url="https://www.coupang.com/vp/products/6497623018?isAddedCart="
    )
    result = await engine.load()

    assert result is not None
    assert result.name is not None
