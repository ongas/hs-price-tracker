import pytest

@pytest.mark.asyncio
async def test_rankingdak_engine_load():
    RankingdakEngine = pytest.importorskip("custom_components.price_tracker.services.rankingdak.engine").RankingdakEngine
    item_url = "https://www.rankingdak.com/product/view?productCd=f000000991"
    engine = RankingdakEngine(item_url=item_url)
    result = await engine.load()
    assert result is not None
    assert getattr(result, "name", None) is not None
