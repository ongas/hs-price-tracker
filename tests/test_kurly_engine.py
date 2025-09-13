import pytest

@pytest.mark.asyncio
async def test_kurly_engine_load():
    KurlyEngine = pytest.importorskip("custom_components.price_tracker.services.kurly.engine").KurlyEngine
    item_url = "https://www.kurly.com/goods/5159822"
    engine = KurlyEngine(item_url=item_url)
    result = await engine.load()
    assert result is not None
    assert getattr(result, "name", None) is not None
