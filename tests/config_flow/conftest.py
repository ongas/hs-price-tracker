import pytest
from homeassistant import config_entries
from custom_components.price_tracker.const import DOMAIN

@pytest.fixture
def mock_config_entry():
    """Mock a config entry for BuyWisely service."""
    return config_entries.ConfigEntry(
        version=1,
        domain=DOMAIN,
        title="Price Tracker - BuyWisely",
        data={
            "service_type": "buywisely",
            "product_url": "https://buywisely.com.au/product/test",
        },
        options={},
        source="user",
        entry_id="test_entry_id",
        unique_id="test_unique_id",
        discovery_keys=[],
        minor_version=1,
    )