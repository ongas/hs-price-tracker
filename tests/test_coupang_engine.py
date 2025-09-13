import pytest

@pytest.mark.asyncio
async def test_coupang_engine_load():
    CoupangEngine = pytest.importorskip("custom_components.price_tracker.services.coupang.engine").CoupangEngine
    item_url = "https://coupang.com/vp/products/6475603839?itemId=14151941530&vendorItemId=81398448965"
    engine = CoupangEngine(item_url=item_url)
    result = await engine.load()
    assert result is not None
    assert getattr(result, "name", None) is not None
