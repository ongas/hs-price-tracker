
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import entity_registry as er, device_registry as dr

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


@pytest.fixture
def mock_config_entry():
    """Mock a ConfigEntry object."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry_id"
    entry.data = {"service_type": "buywisely", "product_url": "http://example.com/product"}
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
        schema=mock_hass.services.async_register.call_args[1]['schema'],
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
    mock_sensor_entity.async_update.assert_awaited_once()


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
    mock_entity = MagicMock(spec=["platform"]) # Does not have async_update
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
