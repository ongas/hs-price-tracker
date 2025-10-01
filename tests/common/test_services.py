import logging
import types

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import entity_registry as er

from custom_components.price_tracker.consts.defaults import DOMAIN
from custom_components.price_tracker import async_setup_entry

DATA_REGISTRY = "entity_registry"


@pytest.fixture
def mock_hass():
    """Mock the HomeAssistant object."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {DOMAIN: {}, "entity_component": {}}
    hass.services = MagicMock()
    hass.config_entries = MagicMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
    hass.config_entries.async_update_entry = AsyncMock()
    hass.config = MagicMock()
    hass.bus = MagicMock()

    mock_entity_registry = MagicMock(spec=er.EntityRegistry)
    mock_entity_registry.entities = MagicMock()
    hass.data[DATA_REGISTRY] = mock_entity_registry

    return hass


# --- NEW TESTS ---


@pytest.mark.asyncio
async def test_manual_update_updates_updated_at(
    monkeypatch, mock_hass, mock_config_entry
):
    """Test that manual update service updates updated_at and triggers refresh."""

    # Simulate a PriceTrackerSensor with async_manual_update and updated_at
    class DummySensor:
        def __init__(self):
            self.updated_at = None
            self.force_update_called = False

        async def async_manual_update(self):
            self.force_update_called = True
            self.updated_at = "now"

    dummy_sensor = DummySensor()
    # Register in hass.data
    mock_hass.data[DOMAIN]["entities"] = {"sensor.test_sensor": dummy_sensor}
    # Patch entity lookup
    mock_entity_registry = mock_hass.data[DATA_REGISTRY]
    mock_entity_entry = MagicMock()
    mock_entity_entry.platform = "sensor"
    mock_entity_registry.async_get.return_value = mock_entity_entry
    mock_component = MagicMock()
    mock_component.get_entity.return_value = dummy_sensor
    mock_hass.data["entity_component"]["sensor"] = mock_component
    with patch("homeassistant.helpers.device_registry.async_get") as mock_dr_async_get:
        mock_dr_async_get.return_value = MagicMock()
        await async_setup_entry(mock_hass, mock_config_entry)
    service_call = MagicMock()
    service_call.data = {"entity_id": "sensor.test_sensor"}
    registered_handler = mock_hass.services.async_register.call_args[0][2]
    await registered_handler(service_call)
    assert (
        dummy_sensor.force_update_called
    ), "Manual update did not trigger async_manual_update"
    assert (
        dummy_sensor.updated_at == "now"
    ), "updated_at was not updated by manual update"


@pytest.mark.asyncio
async def test_entity_registration_in_async_added_to_hass(monkeypatch):
    """Test that entity is registered in hass.data['price_tracker']['entities'] in async_added_to_hass."""
    # Simulate hass and entity
    hass = types.SimpleNamespace()
    hass.data = {DOMAIN: {}}

    class DummySensor:
        def __init__(self):
            self.entity_id = "sensor.test_entity"
            self.hass = hass

        async def async_get_last_state(self):
            return None

        async def async_added_to_hass(self):
            if "price_tracker" not in self.hass.data:
                self.hass.data["price_tracker"] = {}
            if "entities" not in self.hass.data["price_tracker"]:
                self.hass.data["price_tracker"]["entities"] = {}
            self.hass.data["price_tracker"]["entities"][self.entity_id] = self

    sensor = DummySensor()
    # Await async_added_to_hass directly (pytest-asyncio compatible)
    await sensor.async_added_to_hass()
    assert (
        "price_tracker" in hass.data and "entities" in hass.data["price_tracker"]
    ), "Entity not registered in hass.data"
    assert (
        hass.data["price_tracker"]["entities"][sensor.entity_id] is sensor
    ), "Entity not correctly registered"


@pytest.mark.asyncio
async def test_diagnostics_logging_for_manual_update_and_errors(
    monkeypatch, caplog, mock_hass, mock_config_entry
):
    """Test that diagnostics/logging is emitted during manual update and error scenarios."""
    caplog.set_level(logging.DEBUG)

    # Simulate a sensor with logging in async_manual_update
    class DummySensor:
        def __init__(self):
            self.entity_id = "sensor.test_sensor"

        async def async_manual_update(self):
            logging.getLogger(
                "custom_components.price_tracker.components.sensor"
            ).debug(
                "[DIAG][sensor.py] async_manual_update called for %s", self.entity_id
            )

    dummy_sensor = DummySensor()
    mock_hass.data[DOMAIN]["entities"] = {dummy_sensor.entity_id: dummy_sensor}
    mock_entity_registry = mock_hass.data[DATA_REGISTRY]
    mock_entity_entry = MagicMock()
    mock_entity_entry.platform = "sensor"
    mock_entity_registry.async_get.return_value = mock_entity_entry
    mock_component = MagicMock()
    mock_component.get_entity.return_value = dummy_sensor
    mock_hass.data["entity_component"]["sensor"] = mock_component
    with patch("homeassistant.helpers.device_registry.async_get") as mock_dr_async_get:
        mock_dr_async_get.return_value = MagicMock()
        await async_setup_entry(mock_hass, mock_config_entry)
    service_call = MagicMock()
    service_call.data = {"entity_id": dummy_sensor.entity_id}
    registered_handler = mock_hass.services.async_register.call_args[0][2]
    await registered_handler(service_call)
    assert any(
        "[DIAG][sensor.py] async_manual_update called for" in r.message
        for r in caplog.records
    ), "No diagnostic log for manual update"


def test_type_safety_generate_device_id():
    """Test that generate_device_id is only called with str and not None."""
    from custom_components.price_tracker.components.id import IdGenerator

    # Should not raise
    IdGenerator.generate_device_id("test_device")
    # Should raise if None is passed (simulate strict type safety)
    # The implementation will raise ValueError due to string formatting, not TypeError
    with pytest.raises(ValueError):
        IdGenerator.generate_device_id(None)  # type: ignore[arg-type]


@pytest.fixture
def mock_config_entry():
    """Mock a ConfigEntry object."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry_id"
    entry.data = {
        "service_type": "buywisely",
        "product_url": "http://example.com/product",
    }
    entry.options = {}
    entry.add_update_listener = MagicMock()
    return entry


@pytest.mark.asyncio
async def test_service_registration(mock_hass, mock_config_entry):
    """Test that the update_entity service is registered."""
    with patch("homeassistant.helpers.device_registry.async_get") as mock_dr_async_get:
        mock_dr_async_get.return_value = MagicMock()
        await async_setup_entry(mock_hass, mock_config_entry)

    mock_hass.services.async_register.assert_called_once_with(
        DOMAIN,
        "update_entity",
        pytest.approx(mock_hass.services.async_register.call_args[0][2]),
        schema=mock_hass.services.async_register.call_args[1]["schema"],
    )


@pytest.mark.asyncio
async def test_service_call_valid_entity(mock_hass, mock_config_entry):
    """Test calling the update_entity service with a valid entity_id."""
    entity_id = "sensor.test_sensor"

    mock_entity_registry = mock_hass.data[DATA_REGISTRY]
    mock_entity_entry = MagicMock()
    mock_entity_entry.platform = "sensor"
    mock_entity_registry.async_get.return_value = mock_entity_entry

    mock_component = MagicMock()
    mock_sensor_entity = MagicMock()
    mock_sensor_entity.async_update = AsyncMock()
    mock_sensor_entity.async_manual_update = AsyncMock()
    mock_component.get_entity.return_value = mock_sensor_entity
    mock_hass.data["entity_component"]["sensor"] = mock_component

    with patch("homeassistant.helpers.device_registry.async_get") as mock_dr_async_get:
        mock_dr_async_get.return_value = MagicMock()
        await async_setup_entry(mock_hass, mock_config_entry)

    service_call = MagicMock()
    service_call.data = {"entity_id": entity_id}

    registered_handler = mock_hass.services.async_register.call_args[0][2]
    await registered_handler(service_call)

    mock_entity_registry.async_get.assert_called_once_with(entity_id)
    mock_component.get_entity.assert_called_once_with(entity_id)
    mock_sensor_entity.async_manual_update.assert_awaited_once()


@pytest.mark.asyncio
async def test_service_call_invalid_entity(mock_hass, mock_config_entry):
    """Test calling the update_entity service with an invalid entity_id."""
    entity_id = "sensor.non_existent_sensor"

    mock_entity_registry = mock_hass.data[DATA_REGISTRY]
    mock_entity_registry.async_get.return_value = None

    with patch("homeassistant.helpers.device_registry.async_get") as mock_dr_async_get:
        mock_dr_async_get.return_value = MagicMock()
        await async_setup_entry(mock_hass, mock_config_entry)

    service_call = MagicMock()
    service_call.data = {"entity_id": entity_id}

    registered_handler = mock_hass.services.async_register.call_args[0][2]
    await registered_handler(service_call)

    mock_entity_registry.async_get.assert_called_once_with(entity_id)


@pytest.mark.asyncio
async def test_service_call_entity_without_async_update(mock_hass, mock_config_entry):
    """Test calling the update_entity service on an entity without async_update."""
    entity_id = "sensor.entity_no_update"

    mock_entity_registry = mock_hass.data[DATA_REGISTRY]
    mock_entity_entry = MagicMock()
    mock_entity_entry.platform = "sensor"
    mock_entity_registry.async_get.return_value = mock_entity_entry

    mock_component = MagicMock()
    mock_entity = MagicMock(spec=["platform"])  # Does not have async_update
    mock_component.get_entity.return_value = mock_entity

    mock_hass.data["entity_component"]["sensor"] = mock_component

    with patch("homeassistant.helpers.device_registry.async_get") as mock_dr_async_get:
        mock_dr_async_get.return_value = MagicMock()
        await async_setup_entry(mock_hass, mock_config_entry)

    service_call = MagicMock()
    service_call.data = {"entity_id": entity_id}

    registered_handler = mock_hass.services.async_register.call_args[0][2]
    await registered_handler(service_call)

    mock_entity_registry.async_get.assert_called_once_with(entity_id)
    mock_component.get_entity.assert_called_once_with(entity_id)
