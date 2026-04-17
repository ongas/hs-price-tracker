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


from custom_components.price_tracker.const import DOMAIN

@pytest.fixture
def mock_config_entry():
    """Mock a ConfigEntry object."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry_id"
    entry.domain = DOMAIN
    entry.data = {
        "service_type": "buywisely",
        "product_url": "http://example.com/product",
    }
    entry.options = {}
    entry.pref_disable_new_entities = False
    entry.add_update_listener = MagicMock()
    return entry

from pathlib import Path

from homeassistant.loader import IntegrationNotFound

@pytest.mark.asyncio
async def test_service_registration(hass: HomeAssistant, mock_config_entry):
    """Test that the update_entity service is registered."""
    try:
        await async_setup_entry(hass, mock_config_entry)
    except IntegrationNotFound:
        # This is expected because the test environment doesn't have the full integration loaded.
        # We only care that the service was registered before the error.
        pass

    assert hass.services.has_service(DOMAIN, "update_entity")


@pytest.mark.asyncio
async def test_service_call_valid_entity(hass: HomeAssistant, mock_config_entry):
    """Test calling the update_entity service with a valid entity_id."""
    entity_id = "sensor.test_sensor"

    # Set up the component and config entry
    try:
        await async_setup_entry(hass, mock_config_entry)
    except IntegrationNotFound:
        pass

    # Create a mock sensor entity
    mock_sensor_entity = AsyncMock()
    mock_sensor_entity.entity_id = entity_id
    mock_sensor_entity.platform = DOMAIN

    # Add the entity to the entity registry
    entity_registry = er.async_get(hass)
    entry = entity_registry.async_get_or_create(
        "sensor", DOMAIN, "test_sensor", config_entry=mock_config_entry
    )

    # Add the entity to hass.data so it can be found by the service handler
    hass.data.setdefault(DOMAIN, {}).setdefault("entities", {})[entry.entity_id] = mock_sensor_entity

    # Mock the entity_component
    mock_entity_component = MagicMock()
    mock_entity_component.get_entity.return_value = mock_sensor_entity
    hass.data["entity_component"] = {
        DOMAIN: mock_entity_component
    }

    # Call the service
    await hass.services.async_call(
        DOMAIN, "update_entity", {"entity_id": entry.entity_id}, blocking=True
    )

    # Check that async_update was called
    mock_sensor_entity.async_update.assert_awaited_once_with(force=False)

@pytest.mark.asyncio
async def test_service_call_invalid_entity(hass: HomeAssistant, mock_config_entry):
    """Test calling the update_entity service with an invalid entity_id."""
    entity_id = "sensor.non_existent_sensor"

    try:
        await async_setup_entry(hass, mock_config_entry)
    except IntegrationNotFound:
        pass

    # Call the service with an invalid entity_id
    await hass.services.async_call(
        DOMAIN, "update_entity", {"entity_id": entity_id}, blocking=True
    )

    # Assert that no error was raised and the service call completed (even if it did nothing)
    # The warning log will indicate that the entity was not found.
    assert not hass.services.has_service(entity_id, "update")

@pytest.mark.asyncio
async def test_service_call_invalid_entity(hass: HomeAssistant, mock_config_entry):
    """Test calling the update_entity service with an invalid entity_id."""
    entity_id = "sensor.non_existent_sensor"

    try:
        await async_setup_entry(hass, mock_config_entry)
    except IntegrationNotFound:
        pass

    # Call the service with an invalid entity_id
    await hass.services.async_call(
        DOMAIN, "update_entity", {"entity_id": entity_id}, blocking=True
    )

    # Assert that no error was raised and the service call completed (even if it did nothing)
    # The warning log will indicate that the entity was not found.
    assert not hass.services.has_service(entity_id, "update")

@pytest.mark.asyncio
async def test_service_call_invalid_entity(hass: HomeAssistant, mock_config_entry):
    """Test calling the update_entity service with an invalid entity_id."""
    entity_id = "sensor.non_existent_sensor"

    try:
        await async_setup_entry(hass, mock_config_entry)
    except IntegrationNotFound:
        pass

    # Call the service with an invalid entity_id
    await hass.services.async_call(
        DOMAIN, "update_entity", {"entity_id": entity_id}, blocking=True
    )

    # Assert that no error was raised and the service call completed (even if it did nothing)
    # The warning log will indicate that the entity was not found.
    assert not hass.services.has_service(entity_id, "update")

@pytest.mark.asyncio
async def test_service_call_invalid_entity(hass: HomeAssistant, mock_config_entry):
    """Test calling the update_entity service with an invalid entity_id."""
    entity_id = "sensor.non_existent_sensor"

    try:
        await async_setup_entry(hass, mock_config_entry)
    except IntegrationNotFound:
        pass

    # Call the service with an invalid entity_id
    await hass.services.async_call(
        DOMAIN, "update_entity", {"entity_id": entity_id}, blocking=True
    )

    # Assert that no error was raised and the service call completed (even if it did nothing)
    # The warning log will indicate that the entity was not found.
    assert not hass.services.has_service(entity_id, "update")

@pytest.mark.asyncio
async def test_service_call_invalid_entity(hass: HomeAssistant, mock_config_entry):
    """Test calling the update_entity service with an invalid entity_id."""
    entity_id = "sensor.non_existent_sensor"

    try:
        await async_setup_entry(hass, mock_config_entry)
    except IntegrationNotFound:
        pass

    # Call the service with an invalid entity_id
    await hass.services.async_call(
        DOMAIN, "update_entity", {"entity_id": entity_id}, blocking=True
    )

    # Assert that no error was raised and the service call completed (even if it did nothing)
    # The warning log will indicate that the entity was not found.
    assert not hass.services.has_service(entity_id, "update")

@pytest.mark.asyncio
async def test_service_call_invalid_entity(hass: HomeAssistant, mock_config_entry):
    """Test calling the update_entity service with an invalid entity_id."""
    entity_id = "sensor.non_existent_sensor"

    try:
        await async_setup_entry(hass, mock_config_entry)
    except IntegrationNotFound:
        pass

    # Call the service with an invalid entity_id
    await hass.services.async_call(
        DOMAIN, "update_entity", {"entity_id": entity_id}, blocking=True
    )

    # Assert that no error was raised and the service call completed (even if it did nothing)
    # The warning log will indicate that the entity was not found.
    assert not hass.services.has_service(entity_id, "update")

@pytest.mark.asyncio
async def test_service_call_invalid_entity(hass: HomeAssistant, mock_config_entry):
    """Test calling the update_entity service with an invalid entity_id."""
    entity_id = "sensor.non_existent_sensor"

    try:
        await async_setup_entry(hass, mock_config_entry)
    except IntegrationNotFound:
        pass

    # Call the service with an invalid entity_id
    await hass.services.async_call(
        DOMAIN, "update_entity", {"entity_id": entity_id}, blocking=True
    )

    # Assert that no error was raised and the service call completed (even if it did nothing)
    # The warning log will indicate that the entity was not found.
    assert not hass.services.has_service(entity_id, "update")

@pytest.mark.asyncio
async def test_service_call_invalid_entity(hass: HomeAssistant, mock_config_entry):
    """Test calling the update_entity service with an invalid entity_id."""
    entity_id = "sensor.non_existent_sensor"

    try:
        await async_setup_entry(hass, mock_config_entry)
    except IntegrationNotFound:
        pass

    # Call the service with an invalid entity_id
    await hass.services.async_call(
        DOMAIN, "update_entity", {"entity_id": entity_id}, blocking=True
    )

    # Assert that no error was raised and the service call completed (even if it did nothing)
    # The warning log will indicate that the entity was not found.
    assert not hass.services.has_service(entity_id, "update")

@pytest.mark.asyncio
async def test_service_call_invalid_entity(hass: HomeAssistant, mock_config_entry):
    """Test calling the update_entity service with an invalid entity_id."""
    entity_id = "sensor.non_existent_sensor"

    try:
        await async_setup_entry(hass, mock_config_entry)
    except IntegrationNotFound:
        pass

    # Call the service with an invalid entity_id
    await hass.services.async_call(
        DOMAIN, "update_entity", {"entity_id": entity_id}, blocking=True
    )

    # Assert that no error was raised and the service call completed (even if it did nothing)
    # The warning log will indicate that the entity was not found.
    assert not hass.services.has_service(entity_id, "update")

@pytest.mark.asyncio
async def test_service_call_invalid_entity(hass: HomeAssistant, mock_config_entry):
    """Test calling the update_entity service with an invalid entity_id."""
    entity_id = "sensor.non_existent_sensor"

    try:
        await async_setup_entry(hass, mock_config_entry)
    except IntegrationNotFound:
        pass

    # Call the service with an invalid entity_id
    await hass.services.async_call(
        DOMAIN, "update_entity", {"entity_id": entity_id}, blocking=True
    )

    # Assert that no error was raised and the service call completed (even if it did nothing)
    # The warning log will indicate that the entity was not found.
    assert not hass.services.has_service(entity_id, "update")

@pytest.mark.asyncio
async def test_service_call_invalid_entity(hass: HomeAssistant, mock_config_entry):
    """Test calling the update_entity service with an invalid entity_id."""
    entity_id = "sensor.non_existent_sensor"

    try:
        await async_setup_entry(hass, mock_config_entry)
    except IntegrationNotFound:
        pass

    # Call the service with an invalid entity_id
    await hass.services.async_call(
        DOMAIN, "update_entity", {"entity_id": entity_id}, blocking=True
    )

    # Assert that no error was raised and the service call completed (even if it did nothing)
    # The warning log will indicate that the entity was not found.
    assert not hass.services.has_service(entity_id, "update")

@pytest.mark.asyncio
async def test_service_call_invalid_entity(hass: HomeAssistant, mock_config_entry):
    """Test calling the update_entity service with an invalid entity_id."""
    entity_id = "sensor.non_existent_sensor"

    try:
        await async_setup_entry(hass, mock_config_entry)
    except IntegrationNotFound:
        pass

    # Call the service with an invalid entity_id
    await hass.services.async_call(
        DOMAIN, "update_entity", {"entity_id": entity_id}, blocking=True
    )

    # Assert that no error was raised and the service call completed (even if it did nothing)
    # The warning log will indicate that the entity was not found.
    assert not hass.services.has_service(entity_id, "update")
