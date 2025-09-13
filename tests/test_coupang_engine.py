import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock

@pytest.mark.asyncio
async def test_coupang_engine_load():
    CoupangEngine = pytest.importorskip("custom_components.price_tracker.services.coupang.engine").CoupangEngine
    item_url = "https://coupang.com/vp/products/6475603839?itemId=14151941530&vendorItemId=81398448965"
    
    mock_response = {
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
    }

    with patch("custom_components.price_tracker.services.coupang.engine.SafeRequest.request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = MagicMock(data=json.dumps(mock_response), is_not_found=False, has=True)
        engine = CoupangEngine(item_url=item_url)
        result = await engine.load()
        assert result is not None
        assert getattr(result, "name", None) is not None