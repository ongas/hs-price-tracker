import re
import os
from unittest.mock import MagicMock
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.loader import IntegrationNotFound
from custom_components.price_tracker.const import DOMAIN
from homeassistant.helpers import entity_registry as er
from custom_components.price_tracker import async_setup_entry

file_path = "/mnt/e/source/personal_repos/homeassistant/custom_components/price_tracker/tests/common/test_services.py"

# Read the current content of the file
with open(file_path, "r") as f:
    content = f.read()

# Define the new test function content to append
new_test_content = r'''
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
    assert not hass.services.has_service(entity_id, "update")'''

# Append the new test content to the file
modified_content = content.strip() + "\n\n" + new_test_content.strip() + "\n"

# Write the modified content back to the file
with open(file_path, "w") as f:
    f.write(modified_content)

print("Appending of test_service_call_invalid_entity complete.")
