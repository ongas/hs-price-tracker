import pytest

@pytest.mark.asyncio
async def test_ssg_engine_load():
    SsgEngine = pytest.importorskip("custom_components.price_tracker.services.ssg.engine").SsgEngine
    item_url = "https://emart.ssg.com/item/itemView.ssg?itemId=2097001557433&siteNo=6001"
    engine = SsgEngine(item_url=item_url)
    result = await engine.load()
    assert result is not None
    assert getattr(result, "name", None) is not None
