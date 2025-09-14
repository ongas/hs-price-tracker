import pytest
from unittest.mock import MagicMock, AsyncMock
from custom_components.price_tracker.components.sensor import PriceTrackerSensor
from custom_components.price_tracker.datas.item import ItemData, ItemStatus
from custom_components.price_tracker.datas.price import ItemPriceData

@pytest.mark.asyncio
async def test_buywisely_ha_entity_state_and_service():
    # Mock Home Assistant hass object
    mock_hass = MagicMock()
    mock_hass.data = {"price_tracker": {}}
    mock_hass.config = MagicMock()
    mock_hass.config.config_dir = "/tmp/hass_config"
    mock_hass.bus = MagicMock()
    mock_hass.services = MagicMock()
    mock_hass.async_create_task = MagicMock()

    # Create a BuyWisely ItemData
    item_data = ItemData(
        id="test-bw-ha-1",
        name="BuyWisely Product",
        brand="BWBrand",
        url="https://www.buywisely.com.au/product/test-bw-ha-1",
        status=ItemStatus.ACTIVE,
        price=ItemPriceData(price=42.42, currency="AUD"),
        image="http://example.com/image.jpg",
    )

    # Mock engine
    mock_engine = MagicMock()
    mock_engine.load = AsyncMock(return_value=item_data)
    mock_engine.engine_code.return_value = "buywisely"
    mock_engine.id_str.return_value = "test-bw-ha-1"
    mock_engine.entity_id = "test-bw-ha-1"

    # Create sensor entity
    sensor = PriceTrackerSensor(engine=mock_engine)
    sensor.hass = mock_hass
    await sensor.async_added_to_hass()
    await sensor.async_update(force=True)

    # Check state and attributes
    assert sensor.state == 42.42
    assert sensor.unit_of_measurement == "AUD"
    assert sensor.name == "BuyWisely Product"
    assert sensor.entity_picture == "http://example.com/image.jpg"
    attrs = sensor.extra_state_attributes
    assert attrs is not None
    assert attrs.get("price") == 42.42
    assert attrs.get("currency") == "AUD"
    assert attrs.get("name") == "BuyWisely Product"
    assert attrs.get("image") == "http://example.com/image.jpg"
    assert attrs.get("url") == item_data.url
    assert attrs.get("brand") == item_data.brand
    assert attrs.get("status") == item_data.status.name
