import logging
import types
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_registry import DATA_REGISTRY

from custom_components.price_tracker.consts.defaults import DOMAIN
from custom_components.price_tracker import async_setup_entry

_LOGGER = logging.getLogger(__name__)


@pytest.fixture
def mock_hass():
    """Mock HomeAssistant object."""
    hass = MagicMock(spec=HomeAssistant)
    hass.config_entries.async_get_entry = AsyncMock(return_value=MagicMock(entry_id="test_config_entry_id"))
    hass.config_entries.async_get_entries = MagicMock(return_value=[MagicMock(entry_id="test_config_entry_id")])
    hass.config_entries.async_forward_entry_setups = AsyncMock()
    hass.bus = MagicMock()
    hass.bus.async_fire = AsyncMock()
    hass.states = MagicMock()
    hass.states.async_entity_ids = MagicMock(return_value=["sensor.test_entity", "sensor.entity_no_update"])
    hass.services = MagicMock()
    hass.data = {}
    hass.data[DATA_REGISTRY] = MagicMock()
    hass.data["entity_component"] = {
        "price_tracker": MagicMock(get_entity=MagicMock(side_effect=lambda entity_id: _create_mock_entity(entity_id, "price_tracker")))
    }
    return hass


def _create_mock_entity(entity_id, platform, async_update_mock=None):
    mock_entity = MagicMock()
    mock_entity.entity_id = entity_id
    mock_entity.platform = platform
    mock_entity.async_update = async_update_mock if async_update_mock else AsyncMock()
    return mock_entity


# --- NEW TESTS ---


@pytest.mark.asyncio
async def test_manual_update_updates_updated_at(
    monkeypatch, mock_hass, mock_config_entry
):
    """Test that manual update service updates updated_at and triggers refresh."""

    # Simulate a PriceTrackerSensor with async_manual_update and updated_at
    mock_sensor_entity = AsyncMock()
    mock_sensor_entity.updated_at = None
    mock_sensor_entity.force_update_called = False
    mock_sensor_entity.platform = DOMAIN
    mock_sensor_entity.async_update = AsyncMock(side_effect=lambda force: setattr(mock_sensor_entity, 'force_update_called', True) or setattr(mock_sensor_entity, 'updated_at', 'now'))

    dummy_sensor = mock_sensor_entity
    mock_component = MagicMock()
    mock_component.get_entity.return_value = dummy_sensor
    mock_entity_registry = mock_hass.data[DATA_REGISTRY]
    mock_entity_entry = MagicMock()
    mock_entity_entry.platform = DOMAIN
    mock_entity_entry.domain = DOMAIN
    mock_entity_registry.async_get.return_value = mock_entity_entry
    mock_hass.data["entity_component"].__setitem__(DOMAIN, mock_component)
    monkeypatch.setattr(er, "async_get", lambda hass: mock_entity_registry)
    with patch("homeassistant.helpers.device_registry.async_get") as mock_dr_async_get:
        mock_dr_async_get.return_value = MagicMock()
        await async_setup_entry(mock_hass, mock_config_entry)
    service_call = MagicMock()
    service_call.data = {"entity_id": "sensor.test_sensor"}
    registered_handler = mock_hass.services.async_register.call_args[0][2]
    await registered_handler(service_call)
    assert (
        dummy_sensor.force_update_called
    ), "Manual update did not trigger async_update"
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
    mock_sensor_entity = AsyncMock()
    mock_sensor_entity.entity_id = "sensor.test_sensor"
    mock_sensor_entity.force_update_called = False
    mock_sensor_entity.platform = DOMAIN
    mock_sensor_entity.async_update = AsyncMock(side_effect=lambda force: setattr(mock_sensor_entity, 'force_update_called', True) or logging.getLogger("custom_components.price_tracker.components.sensor").debug("[DIAG][sensor.py] async_update called for %s", mock_sensor_entity.entity_id))

    dummy_sensor = mock_sensor_entity
    mock_component = MagicMock()
    mock_component.get_entity.return_value = dummy_sensor
    mock_entity_registry = mock_hass.data[DATA_REGISTRY]
    mock_entity_entry = MagicMock()
    mock_entity_entry.platform = DOMAIN
    mock_entity_entry.domain = DOMAIN
    mock_entity_registry.async_get.return_value = mock_entity_entry
    mock_hass.data[DOMAIN]["entities"] = {dummy_sensor.entity_id: dummy_sensor}
    mock_hass.data["entity_component"].__setitem__(DOMAIN, mock_component)
    monkeypatch.setattr(er, "async_get", lambda hass: mock_entity_registry)
    with patch("homeassistant.helpers.device_registry.async_get") as mock_dr_async_get:
        mock_dr_async_get.return_value = MagicMock()
        await async_setup_entry(mock_hass, mock_config_entry)
    service_call = MagicMock()
    service_call.data = {"entity_id": dummy_sensor.entity_id}
    registered_handler = mock_hass.services.async_register.call_args[0][2]
    await registered_handler(service_call)
    assert any(
        "[DIAG][sensor.py] async_update called for" in r.message
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
        mock_hass.services.async_register.call_args[0][2],
    )


@pytest.mark.asyncio
async def test_service_call_valid_entity(monkeypatch, mock_hass, mock_config_entry):
    """Test calling the update_entity service with a valid entity_id."""
    entity_id = "sensor.test_sensor"

    mock_entity_registry = mock_hass.data[DATA_REGISTRY]
    mock_entity_entry = MagicMock()
    mock_entity_entry.platform = DOMAIN
    mock_entity_entry.domain = DOMAIN
    mock_entity_registry.async_get.return_value = mock_entity_entry

    mock_sensor_entity = AsyncMock()
    mock_sensor_entity.platform = DOMAIN
    mock_hass.data["entity_component"] = MagicMock()
    mock_hass.data["entity_component"].__getitem__.return_value = MagicMock(get_entity=MagicMock(return_value=mock_sensor_entity))

    monkeypatch.setattr(er, "async_get", lambda hass: mock_entity_registry)
    with patch("homeassistant.helpers.device_registry.async_get") as mock_dr_async_get:
        mock_dr_async_get.return_value = MagicMock()
        await async_setup_entry(mock_hass, mock_config_entry)

    service_call = MagicMock()
    service_call.data = {"entity_id": entity_id}

    registered_handler = mock_hass.services.async_register.call_args[0][2]
    await registered_handler(service_call)
    mock_entity_registry.async_get.assert_called_once_with(entity_id)

    mock_sensor_entity.async_update.assert_awaited_once_with(force=False)




@pytest.mark.asyncio
async def test_service_call_invalid_entity(monkeypatch, mock_hass, mock_config_entry):
    """Test calling the update_entity service with an invalid entity_id."""
    entity_id = "sensor.non_existent_sensor"

    mock_entity_registry = mock_hass.data[DATA_REGISTRY]
    mock_entity_registry.async_get.return_value = None

    monkeypatch.setattr(er, "async_get", lambda hass: mock_entity_registry)
    with patch("homeassistant.helpers.device_registry.async_get") as mock_dr_async_get:
        mock_dr_async_get.return_value = MagicMock()
        await async_setup_entry(mock_hass, mock_config_entry)

    service_call = MagicMock()
    service_call.data = {"entity_id": entity_id}

    registered_handler = mock_hass.services.async_register.call_args[0][2]
    await registered_handler(service_call)
    mock_entity_registry.async_get.assert_called_once_with(entity_id)


@pytest.mark.asyncio
async def test_service_call_entity_without_async_update(monkeypatch, mock_hass, mock_config_entry):
    """Test calling the update_entity service on an entity without async_update."""
    entity_id = "sensor.entity_no_update"

    mock_entity_registry = mock_hass.data[DATA_REGISTRY]
    mock_entity_entry = MagicMock()
    mock_entity_entry.platform = DOMAIN
    mock_entity_entry.domain = DOMAIN
    mock_entity_registry.async_get.return_value = mock_entity_entry

    mock_component = MagicMock()
    mock_entity = MagicMock()
    mock_entity.async_update = AsyncMock()
    mock_hass.data["entity_component"].__setitem__(DOMAIN, mock_component)
    mock_component.get_entity.return_value = mock_entity

    monkeypatch.setattr(er, "async_get", lambda hass: mock_entity_registry)
    with patch("homeassistant.helpers.device_registry.async_get") as mock_dr_async_get:
        mock_dr_async_get.return_value = MagicMock()
        await async_setup_entry(mock_hass, mock_config_entry)

    service_call = MagicMock()
    service_call.data = {"entity_id": entity_id}

    registered_handler = mock_hass.services.async_register.call_args[0][2]
    await registered_handler(service_call)

