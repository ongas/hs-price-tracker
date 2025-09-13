import voluptuous as vol
import pytest
import sys
import os
from unittest.mock import MagicMock, AsyncMock
# Add both possible package roots to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../custom_components/price_tracker/custom_components/price_tracker')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../custom_components/price_tracker')))
from custom_components.price_tracker.config_flow import PriceTrackerConfigFlow
from custom_components.price_tracker.datas.item import ItemData, ItemStatus
from custom_components.price_tracker.datas.price import ItemPriceData
from datetime import datetime

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
    mock_hass.services = MagicMock()

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

@pytest.mark.asyncio
async def test_lowest_price_populates_ha_entity(monkeypatch):
    """Test that the lowest price from the engine populates the HA entity state and attributes."""
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from custom_components.price_tracker.components.sensor import PriceTrackerSensor

    # Mock hass object
    mock_hass = MagicMock(spec=HomeAssistant)
    mock_hass.data = {"price_tracker": {}}
    mock_hass.config = MagicMock()
    mock_hass.config.config_dir = "/tmp/hass_config"
    mock_hass.bus = MagicMock()
    mock_hass.services = MagicMock()

    # Mock entity and device registries
    mock_entity_registry = MagicMock()
    mock_entity_registry.entities.get_entries_for_config_entry_id.return_value = []
    monkeypatch.setattr("homeassistant.helpers.entity_registry.async_get", MagicMock(return_value=mock_entity_registry))

    mock_device_registry = MagicMock()
    mock_device_registry.async_entries_for_config_entry.return_value = []
    monkeypatch.setattr("homeassistant.helpers.device_registry.async_get", MagicMock(return_value=mock_device_registry))

    # Mock config_entry
    mock_config_entry = MagicMock(spec=ConfigEntry)
    mock_config_entry.entry_id = "test_entry_id_lowest_price"
    mock_config_entry.data = {"service_type": "buywisely", "product_url": "https://www.buywisely.com.au/product/test-product-lowest-price"}
    mock_config_entry.options = {}

    mock_config_entry.add_update_listener = MagicMock()
    mock_hass.config_entries.async_update_entry = AsyncMock()
    mock_hass.config_entries.async_forward_entry_setups = AsyncMock()

    # Mock the ItemData that the engine.load() should return
    mock_lowest_price = 123.45
    mock_currency = "USD"
    mock_product_name = "Test Product Lowest Price"
    mock_image_url = "http://example.com/image.jpg"

    mock_item_data = ItemData(
        id="test-product-lowest-price",
        name=mock_product_name,
        brand="TestBrand",
        url="https://www.buywisely.com.au/product/test-product-lowest-price",
        status=ItemStatus.ACTIVE,
        price=ItemPriceData(price=mock_lowest_price, currency=mock_currency),
        image=mock_image_url,
    )

    # Mock the engine's load method to return our mock_item_data
    mock_engine_instance = MagicMock()
    mock_engine_instance.load = AsyncMock(return_value=mock_item_data)
    mock_engine_instance.engine_code.return_value = "buywisely"
    mock_engine_instance.id_str.return_value = "test-product-lowest-price"
    mock_engine_instance.entity_id = "test-product-lowest-price"



    # Patch the BuyWiselyEngine constructor in the service engine mapping directly for the entire test
    import custom_components.price_tracker.services.factory as factory_mod
    original_service_item_engine = factory_mod._SERVICE_ITEM_ENGINE.copy()
    factory_mod._SERVICE_ITEM_ENGINE["buywisely"] = lambda **kwargs: mock_engine_instance

    try:
        from custom_components.price_tracker import async_setup_entry as init_async_setup_entry
        from custom_components.price_tracker.sensor import async_setup_entry as sensor_async_setup_entry

        mock_hass.data["price_tracker"][mock_config_entry.entry_id] = mock_config_entry.data

        result_init = await init_async_setup_entry(mock_hass, mock_config_entry)
        assert result_init is True

        mock_async_add_entities = AsyncMock()
        await sensor_async_setup_entry(mock_hass, mock_config_entry, mock_async_add_entities)
        print(f"DIAGNOSTIC: mock_async_add_entities.call_args_list: {mock_async_add_entities.call_args_list}")

        # Assert that entities were added
        # We expect two calls to async_add_entities, one for devices (empty) and one for sensors.
        # We need to get the sensor entity from the second call.
        assert mock_async_add_entities.call_count == 2
        added_entities = mock_async_add_entities.call_args_list[1][0][0]
        assert len(added_entities) == 1
        sensor_entity = added_entities[0]

        # Ensure it's a PriceTrackerSensor instance
        assert isinstance(sensor_entity, PriceTrackerSensor)
        print(f"DIAGNOSTIC: sensor_entity: {sensor_entity}")
        print(f"DIAGNOSTIC: sensor_entity._engine: {getattr(sensor_entity, '_engine', None)}")

        # Set _updated_at to an old date to force update
        sensor_entity._updated_at = datetime(2000, 1, 1)

        # Manually trigger update to ensure state is set (async_add_entities doesn't always trigger it immediately in tests)
        await sensor_entity.async_update()
        print(f"DIAGNOSTIC: sensor_entity.state: {sensor_entity.state}")
        print(f"DIAGNOSTIC: sensor_entity._item_data: {sensor_entity._item_data}")
        if sensor_entity._item_data is not None:
            print(f"DIAGNOSTIC: sensor_entity._item_data.price: {sensor_entity._item_data.price}")
            if sensor_entity._item_data.price is not None:
                print(f"DIAGNOSTIC: sensor_entity._item_data.price.price: {sensor_entity._item_data.price.price}")
            else:
                print("DIAGNOSTIC: sensor_entity._item_data.price is None")
        else:
            print("DIAGNOSTIC: sensor_entity._item_data is None")

        # Assert the state and attributes
        assert sensor_entity.state == mock_lowest_price
        assert sensor_entity.unit_of_measurement == mock_currency
        assert sensor_entity.name == mock_product_name
        assert sensor_entity.entity_picture == mock_image_url
        assert sensor_entity.extra_state_attributes is not None
        assert sensor_entity.extra_state_attributes.get("price") == mock_lowest_price
        assert sensor_entity.extra_state_attributes.get("currency") == mock_currency
        assert sensor_entity.extra_state_attributes.get("name") == mock_product_name
        assert sensor_entity.extra_state_attributes.get("image") == mock_image_url
        assert sensor_entity.extra_state_attributes.get("url") == mock_item_data.url
        assert sensor_entity.extra_state_attributes.get("brand") == mock_item_data.brand
        assert sensor_entity.extra_state_attributes.get("status") == mock_item_data.status.name
    finally:
        factory_mod._SERVICE_ITEM_ENGINE = original_service_item_engine
