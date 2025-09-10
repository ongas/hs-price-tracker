import logging

from homeassistant import config_entries, core

from .components.sensor import PriceTrackerSensor
from .consts.confs import (
    CONF_DEVICE,
    CONF_ITEM_UNIT_TYPE,
    CONF_ITEM_UNIT,
    CONF_ITEM_REFRESH_INTERVAL,
    CONF_ITEM_MANAGEMENT_CATEGORY,
    CONF_PROXY,
    CONF_PROXY_OPENSOURCE,
    CONF_SELENIUM,
    CONF_SELENIUM_PROXY,
    CONF_DEBUG,
    CONF_ITEM_MANAGEMENT_CATEGORIES,
)
from .consts.defaults import DOMAIN
from .datas.unit import ItemUnitType
from .services.factory import create_service_device_generator, create_service_engine
from .utilities.list import Lu

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    config = hass.data[DOMAIN][config_entry.entry_id]
    service_type = config['service_type']



    _LOGGER.info("[DIAG][sensor.py] async_setup_entry called for entry_id=%s, config=%s", config_entry.entry_id, config)

    if config_entry.options:
        config.update(config_entry.options)

    devices = {}
    sensors = []
    proxy = Lu.get_or_default(config, CONF_PROXY, None)
    proxy_opensource = Lu.get_or_default(config, CONF_PROXY_OPENSOURCE, False)
    selenium = Lu.get_or_default(config, CONF_SELENIUM, None)
    selenium_proxy = Lu.get_or_default(config, CONF_SELENIUM_PROXY, None)

    if CONF_DEVICE in config:
        for device in config[CONF_DEVICE]:
            # Get device generator
            device_generator = create_service_device_generator(service_type)
            if device_generator:
                target_device = device_generator(
                    {
                        **device,
                        "entry_id": config_entry.entry_id,
                    }
                )
                devices = {**devices, **{target_device.device_id: target_device}}
    _LOGGER.info("[DIAG][sensor.py] Devices generated: %s", devices)
    async_add_entities(list(devices.values()), update_before_add=True)

    item_url = config['product_url']
    device = None # Assuming no device is configured directly for now

    try:
        _LOGGER.info("[DIAG][sensor.py] Registering sensor for item_url: %s, proxy: %s, proxy_opensource: %s", item_url, proxy, proxy_opensource)

        engine = create_service_engine(service_type)(
            item_url=item_url,
            proxies=proxy,
            device=device,
            selenium=selenium,
            selenium_proxy=selenium_proxy,
        )
        _LOGGER.info("[DIAG][sensor.py] Created engine: %s, engine.id_str(): %s, engine.entity_id: %s", engine, getattr(engine, 'id_str', lambda: None)(), getattr(engine, 'entity_id', None))
        sensor = PriceTrackerSensor(
            engine=engine,
            device=device,
            unit_type=ItemUnitType.of(Lu.get(config, CONF_ITEM_UNIT_TYPE, "auto")) # Use config directly
            if Lu.get(config, CONF_ITEM_UNIT_TYPE, "auto") != "auto"
            else ItemUnitType.PIECE,
            unit_value=Lu.get(config, CONF_ITEM_UNIT, 1), # Use config directly
            refresh_period=Lu.get(config, CONF_ITEM_REFRESH_INTERVAL, 30), # Use config directly
            management_category=Lu.get(config, CONF_ITEM_MANAGEMENT_CATEGORY, None), # Use config directly
            management_categories=Lu.get(
                config, CONF_ITEM_MANAGEMENT_CATEGORIES, None
            ), # Use config directly
            debug=Lu.get_or_default(config, CONF_DEBUG, False),
        )
        _LOGGER.info("[DIAG][sensor.py] Created sensor: %s, sensor.entity_id: %s, sensor._attr_unique_id: %s", sensor, getattr(sensor, 'entity_id', None), getattr(sensor, '_attr_unique_id', None))

        sensors.append(sensor)

    except Exception as e:
        _LOGGER.exception("[DIAG][sensor.py] Sensor configuration error: %s", e)

    _LOGGER.info("[DIAG][sensor.py] Calling async_add_entities with sensors: %s", sensors)
    async_add_entities(sensors, update_before_add=True)


async def update_listener(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> None:
    """Update listener."""
    await hass.config_entries.async_reload(entry.entry_id)
