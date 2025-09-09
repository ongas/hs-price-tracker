import voluptuous as vol
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
    monkeypatch.setattr("custom_components.price_tracker.services.setup.price_tracker_setup_init", lambda hass: vol.Schema({"lang": "en"}))

    # Mock the _KIND dictionary directly
    mock_kind = {
        "buywisely": "Buywisely",
        "coupang": "Coupang (Korea)",
    }
    monkeypatch.setattr("custom_components.price_tracker.services.setup._KIND", mock_kind)


    flow = PriceTrackerConfigFlow()
    flow.hass = mock_hass

    # Mock async_set_unique_id to prevent TypeError
    monkeypatch.setattr(flow, "async_set_unique_id", AsyncMock())

    # Step 1: Service selection
    result = await flow.async_step_service_selection(None)
    assert result.get("type") == "form"
    assert result.get("step_id") == "service_selection"

    # Step 2: Product details (for buywisely)
    user_input_step1 = {"service_type": "buywisely", "lang": "en"}
    result = await flow.async_step_service_selection(user_input_step1)
    assert result.get("type") == "form"
    assert result.get("step_id") == "user"

    # Step 3: Submit product details for buywisely
    user_input_step2 = {
        "product_url": "https://buywisely.com.au/product/sony-wh-1000xm4-wireless-noise-cancelling-headphones-black-1?id=12345"
    }
    result = await flow.async_step_user(user_input_step2)
    assert result["type"] == "create_entry"
    assert result["title"] == mock_kind[user_input_step1["service_type"]]
    assert result["data"]["service_type"] == "buywisely"
    assert result["data"]["product_url"] == user_input_step2["product_url"]

    # Test for other service (product_url should not be required)
    user_input_step1_other = {"service_type": "coupang", "lang": "en"}
    result = await flow.async_step_service_selection(user_input_step1_other)
    assert result.get("type") == "form"
    assert result.get("step_id") == "user"

    user_input_step2_other = {} # No product_url needed
    result = await flow.async_step_user(user_input_step2_other)
    assert result["type"] == "create_entry"
    assert result["title"] == mock_kind[user_input_step1_other["service_type"]]
    assert result["data"]["service_type"] == "coupang"
    assert "product_url" not in result["data"]

# @pytest.mark.asyncio
# async def test_config_flow_reconfigure_and_import(monkeypatch):
#     mock_hass = MagicMock()
#     mock_hass.config.language = "en"
#     monkeypatch.setattr("custom_components.price_tracker.services.setup.price_tracker_setup_init", lambda hass: vol.Schema({"lang": "en"}))
#     mock_kind = {
#         "buywisely": "Buywisely",
#         "coupang": "Coupang (Korea)",
#     }
#     monkeypatch.setattr("custom_components.price_tracker.services.setup._KIND", mock_kind)

#     flow = PriceTrackerConfigFlow()
#     flow.hass = mock_hass
#     monkeypatch.setattr(flow, "async_set_unique_id", AsyncMock())

#     # Test async_step_reconfigure
#     # Simulate an existing config entry
#     mock_config_entry = MagicMock()
#     mock_config_entry.data = {"service_type": "buywisely", "product_url": "http://example.com/old"}
#     flow.config_entry = mock_config_entry

#     result = await flow.async_step_reconfigure(None)
#     assert result.get("type") == "form"
#     assert result.get("step_id") == "service_selection"

#     # Simulate user selecting a service (e.g., buywisely)
#     user_input_step1 = {"service_type": "buywisely", "lang": "en"}
#     result = await flow.async_step_service_selection(user_input_step1)
#     assert result.get("type") == "form"
#     assert result.get("step_id") == "user"

#     # Simulate user providing product URL
#     user_input_step2 = {"product_url": "http://example.com/new"}
#     result = await flow.async_step_user(user_input_step2)
#     assert result["type"] == "create_entry" # Should be create_entry or update_entry
#     # For reconfigure, it should ideally be an update_entry, but the current code creates a new one.
#     # This test will pass if it creates an entry without error.

#     # Test async_step_import
#     import_info = {"service_type": "coupang", "lang": "en", "product_url": "http://example.com/imported"}
#     result = await flow.async_step_import(import_info)
#     assert result["type"] == "create_entry"
#     assert result["data"]["service_type"] == "coupang"
#     assert result["data"]["product_url"] == "http://example.com/imported"

@pytest.mark.asyncio
async def test_async_setup_entry_service_type_handling(monkeypatch):
    """Test that async_setup_entry correctly handles 'service_type' from config_entry.data."""
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

    # Mock hass object
    mock_hass = MagicMock(spec=HomeAssistant)
    mock_hass.data = {"price_tracker": {}} # Initialize hass.data for DOMAIN
    mock_hass.config = MagicMock()
    mock_hass.config.config_dir = "/tmp/hass_config"
    mock_hass.bus = MagicMock() # Add this line to mock the bus attribute

    # Mock entity and device registries
    mock_entity_registry = MagicMock()
    mock_entity_registry.entities.get_entries_for_config_entry_id.return_value = [] # Mock the method called
    monkeypatch.setattr("homeassistant.helpers.entity_registry.async_get", MagicMock(return_value=mock_entity_registry))

    mock_device_registry = MagicMock()
    mock_device_registry.async_entries_for_config_entry.return_value = [] # Mock the method called
    monkeypatch.setattr("homeassistant.helpers.device_registry.async_get", MagicMock(return_value=mock_device_registry))

    # Mock config_entry
    mock_config_entry = MagicMock(spec=ConfigEntry)
    mock_config_entry.entry_id = "test_entry_id"
    mock_config_entry.data = {"service_type": "buywisely", "product_url": "http://example.com/product"}
    mock_config_entry.options = {} # Ensure options is not None

    # Mock async_update_entry to prevent errors during setup
    mock_config_entry.add_update_listener = MagicMock()
    mock_hass.config_entries.async_update_entry = AsyncMock()
    mock_hass.config_entries.async_forward_entry_setups = AsyncMock()

    # Mock the actual async_setup_entry from __init__.py
    # We need to import it directly to call it
    from custom_components.price_tracker import async_setup_entry as init_async_setup_entry

    # Mock the actual async_setup_entry from sensor.py
    from custom_components.price_tracker.sensor import async_setup_entry as sensor_async_setup_entry

    # Patch hass.data[DOMAIN][entry.entry_id] to be the config_entry.data
    # This simulates how sensor.py gets its config
    mock_hass.data["price_tracker"][mock_config_entry.entry_id] = mock_config_entry.data

    # Call async_setup_entry from __init__.py
    # This should process the config_entry and store data in hass.data
    result_init = await init_async_setup_entry(mock_hass, mock_config_entry)
    assert result_init is True # Should return True on successful setup

    # Now call async_setup_entry from sensor.py
    # This is where the KeyError previously occurred
    mock_async_add_entities = AsyncMock()
    await sensor_async_setup_entry(mock_hass, mock_config_entry, mock_async_add_entities)

    # Assert that no KeyError occurred and entities were attempted to be added
    mock_async_add_entities.assert_called()
    # You might add more specific assertions here, e.g., checking the type of entities added
