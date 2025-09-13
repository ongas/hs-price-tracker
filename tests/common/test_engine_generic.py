import pytest

# Parameterized engine test for all supported services
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "engine_cls,item_url",
    [
        pytest.param(
            pytest.importorskip("custom_components.price_tracker.services.coupang.engine").CoupangEngine,
            "https://coupang.com/vp/products/6475603839?itemId=14151941530&vendorItemId=81398448965",
            id="coupang-1",
        ),
        pytest.param(
            pytest.importorskip("custom_components.price_tracker.services.kurly.engine").KurlyEngine,
            "https://www.kurly.com/goods/5159822",
            id="kurly-1",
        ),
        pytest.param(
            pytest.importorskip("custom_components.price_tracker.services.rankingdak.engine").RankingdakEngine,
            "https://www.rankingdak.com/product/view?productCd=f000000991",
            id="rankingdak-1",
        ),
        pytest.param(
            pytest.importorskip("custom_components.price_tracker.services.smartstore.engine").SmartstoreEngine,
            "https://m.brand.naver.com/hbafstore/products/9132075573",
            id="smartstore-1",
        ),
        pytest.param(
            pytest.importorskip("custom_components.price_tracker.services.ssg.engine").SsgEngine,
            "https://emart.ssg.com/item/itemView.ssg?itemId=2097001557433&siteNo=6001",
            id="ssg-1",
        ),
    ],
)
async def test_engine_load(engine_cls, item_url):
    engine = engine_cls(item_url=item_url)
    result = await engine.load()
    assert result is not None
    assert getattr(result, "name", None) is not None
