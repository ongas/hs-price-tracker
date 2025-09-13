import pytest

@pytest.mark.asyncio
async def test_smartstore_engine_load():
    SmartstoreEngine = pytest.importorskip("custom_components.price_tracker.services.smartstore.engine").SmartstoreEngine
    item_url = "https://m.brand.naver.com/hbafstore/products/9132075573"
    engine = SmartstoreEngine(item_url=item_url)
    result = await engine.load()
    assert result is not None
    assert getattr(result, "name", None) is not None
