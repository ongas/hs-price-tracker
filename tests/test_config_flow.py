import pytest
from homeassistant import config_entries
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../custom_components/price_tracker/custom_components/price_tracker')))
from config_flow import PriceTrackerConfigFlow

@pytest.mark.asyncio
async def test_config_flow_guided(monkeypatch):
    flow = PriceTrackerConfigFlow()
    # Step 1: Service selection
    result = await flow.async_step_user(None)
    assert result["type"] == "form"
    assert result["step_id"] == "user"
    # Step 2: Product details
    user_input = {"service_type": "buywisely", "lang": "en"}
    result = await flow.async_step_user(user_input)
    assert result["type"] == "form"
    assert result["step_id"] == "product_details"
    # Step 3: Submit product details
    product_input = {
        "item_url": "https://buywisely.com.au/product/sony-wh-1000xm4-wireless-noise-cancelling-headphones-black-1?id=12345",
        "item_unique_id": "test-unique-id",
        "item_device_id": "test-device-id",
        "item_management_category": "audio",
        "item_unit_type": "auto",
        "item_unit": "1",
        "item_refresh_interval": 30,
        "item_price_change_interval_hour": 24,
        "item_debug": False,
        "proxy": "",
        "selenium": "",
        "selenium_proxy": ""
    }
    result = await flow.async_step_product_details(product_input)
    assert result["type"] == "create_entry"
    assert result["title"] == "BuyWisely"
    assert result["data"]["item_url"] == product_input["item_url"]
    assert result["data"]["item_unique_id"] == product_input["item_unique_id"]
