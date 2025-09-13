import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock

# Parameterized engine test for all supported services
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "engine_cls,item_url,mock_response",
    [
        pytest.param(
            pytest.importorskip("custom_components.price_tracker.services.coupang.engine").CoupangEngine,
            "https://coupang.com/vp/products/6475603839?itemId=14151941530&vendorItemId=81398448965",
            {
                "rCode": "RET0000",
                "rData": {
                    "pageList": [
                        {
                            "page": "PAGE_ATF",
                            "widgetList": [
                                {
                                    "entity": {
                                        "viewType": "PRODUCT_DETAIL_PRODUCT_INFO",
                                        "title": [
                                            {
                                                "text": "Test Product"
                                            }
                                        ]
                                    }
                                }
                            ]
                        },
                        {
                            "page": "PAGE_HANDLEBAR",
                            "widgetList": [
                                {
                                    "entity": {
                                        "viewType": "PRODUCT_DETAIL_HANDLEBAR_QUANTITY",
                                        "deliveryDate": []
                                    }
                                },
                                {
                                    "entity": {
                                        "viewType": "PRODUCT_DETAIL_BASE_INFO",
                                        "deliveryInfo": {
                                            "shippingFee": []
                                        },
                                        "priceInfo": {
                                            "finalPrice": {
                                                "0": 0
                                            },
                                            "originalPrice": {
                                                "0": 0
                                            }
                                        }
                                    }
                                }
                            ]
                        }
                    ]
                }
            },
            id="coupang-1",
        ),
        pytest.param(
            pytest.importorskip("custom_components.price_tracker.services.kurly.engine").KurlyEngine,
            "https://www.kurly.com/goods/5159822",
            None,
            id="kurly-1",
        ),
        pytest.param(
            pytest.importorskip("custom_components.price_tracker.services.rankingdak.engine").RankingdakEngine,
            "https://www.rankingdak.com/product/view?productCd=f000000991",
            None,
            id="rankingdak-1",
        ),
        pytest.param(
            pytest.importorskip("custom_components.price_tracker.services.smartstore.engine").SmartstoreEngine,
            "https://m.brand.naver.com/hbafstore/products/9132075573",
            None,
            id="smartstore-1",
        ),
        pytest.param(
            pytest.importorskip("custom_components.price_tracker.services.ssg.engine").SsgEngine,
            "https://emart.ssg.com/item/itemView.ssg?itemId=2097001557433&siteNo=6001",
            None,
            id="ssg-1",
        ),
    ],
)
async def test_engine_load(engine_cls, item_url, mock_response):
    if mock_response:
        with patch("custom_components.price_tracker.services.coupang.engine.SafeRequest.request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = MagicMock(data=json.dumps(mock_response), is_not_found=False, has=True)
            engine = engine_cls(item_url=item_url)
            result = await engine.load()
            assert result is not None
            assert getattr(result, "name", None) is not None
    else:
        engine = engine_cls(item_url=item_url)
        result = await engine.load()
        assert result is not None
        assert getattr(result, "name", None) is not None
