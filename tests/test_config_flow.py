import pytest
import sys
import os
from unittest.mock import MagicMock, AsyncMock
# Add both possible package roots to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../custom_components/price_tracker/custom_components/price_tracker')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../custom_components/price_tracker')))
from custom_components.price_tracker.config_flow import PriceTrackerConfigFlow

@pytest.mark.asyncio
async def test_config_flow_guided(monkeypatch):
    # Mock the hass object and its config.language attribute
    mock_hass = MagicMock()
    mock_hass.config.language = "en"
    monkeypatch.setattr("custom_components.price_tracker.services.setup.price_tracker_setup_init", lambda hass: {"lang": "en"})
    monkeypatch.setattr("custom_components.price_tracker.services.setup.Lang", lambda hass: MagicMock(selector=lambda: {"lang": "en"}))

    flow = PriceTrackerConfigFlow()
    flow.hass = mock_hass

    # Mock async_set_unique_id to prevent TypeError
    monkeypatch.setattr(flow, "async_set_unique_id", AsyncMock())

    # Step 1: Service selection
    result = await flow.async_step_user(None)
    assert result.get("type") == "form"
    assert result.get("step_id") == "user"
    # Step 2: Product details
    user_input = {"service_type": "buywisely", "lang": "en"}
    result = await flow.async_step_user(user_input)
    assert result.get("type") == "form"
    assert result.get("step_id") == "product_url"
    # Step 3: Submit product details
    product_input = {
        "product_url": "https://buywisely.com.au/product/sony-wh-1000xm4-wireless-noise-cancelling-headphones-black-1?id=12345"
    }
    result = await flow.async_step_product_url(product_input)
    assert result["type"] == "create_entry"
    assert result["title"] == "Price Tracker"
    assert result["data"]["product_url"] == product_input["product_url"]