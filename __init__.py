from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    device_registry as dr,
    entity_registry as er,
)

from custom_components.price_tracker.components.id import IdGenerator
from custom_components.price_tracker.consts.confs import (
    CONF_ITEM_DEVICE_ID,
    CONF_ITEM_UNIQUE_ID,
    CONF_ITEM_URL,
)
from custom_components.price_tracker.consts.defaults import DOMAIN, PLATFORMS
from custom_components.price_tracker.services.factory import (
    create_service_item_url_parser,
    create_service_item_target_parser,
    create_service_device_parser_and_parse,
    has_service_item_target_parser,
)
from custom_components.price_tracker.utilities.list import Lu

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the price tracker component."""
    _LOGGER.debug("Setting up price tracker component {}".format(config))
    hass.data.setdefault(DOMAIN, {})

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.info("[DIAG][%s] async_setup_entry ENTRYPOINT -- this should always log!", datetime.now().isoformat())
    _LOGGER.info("[DIAG][%s] async_setup_entry called for entry_id=%s, type=%s", datetime.now().isoformat(), entry.entry_id, entry.data.get("type"))
    _LOGGER.info("[DIAG][%s] async_setup_entry config entry data: %s", datetime.now().isoformat(), entry.data)
    _LOGGER.info("[DIAG][%s] async_setup_entry config entry options: %s", datetime.now().isoformat(), entry.options)
    _LOGGER.debug("Setting up entry and data {} > {}".format(entry, entry.data))
    _LOGGER.debug("Setting up entry and options {} > {}".format(entry, entry.options))

    # For upgrade options (1.4.0)
    if not has_service_item_target_parser(entry.data["type"]):
        return False

    # For upgrade options (1.0.0)
    if entry.data is not None and "device" in entry.data:
        """Update device_id"""
        data = {
            **entry.data,
            "device": Lu.map(
                entry.data["device"],
                lambda x: {
                    **x,
                    CONF_ITEM_DEVICE_ID: (
                        IdGenerator.generate_device_id(
                            device_target
                        ) if (device_target := create_service_device_parser_and_parse(entry.data["type"], x)) is not None else x.get(CONF_ITEM_DEVICE_ID, "")
                    ),
                },
            ),
        }
    else:
        data = entry.data

    if entry.options is not None and "target" in entry.options:
        options = {
            **entry.options,
            "target": Lu.map(
                entry.options["target"],
                lambda x: {
                    **x,
                    CONF_ITEM_DEVICE_ID: Lu.get(x, "device")
                    if Lu.get(x, "device") is not None
                    else Lu.get(x, CONF_ITEM_DEVICE_ID),
                },
            ),
        }

        """Update item_url (item_unique_id)"""
        options = {
            **options,
            "target": Lu.map(
                options["target"],
                lambda x: {
                    **x,
                    CONF_ITEM_UNIQUE_ID: IdGenerator.generate_entity_id(
                        service_type=entry.data["type"],
                        entity_target=create_service_item_target_parser(
                            entry.data["type"]
                        )({"item_url": x[CONF_ITEM_URL]}),
                        device_id=IdGenerator.get_device_target_from_id(
                            Lu.get(x, CONF_ITEM_DEVICE_ID)
                        )
                        if Lu.get(x, CONF_ITEM_DEVICE_ID) is not None
                        else None,
                    ),
                },
            ),
        }
    else:
        options = {"target": data.get("target", [])}


    # Enhanced diagnostics: log final config and options before forwarding
    _LOGGER.info("[DIAG][%s] FINAL config data for entry_id=%s: %s", datetime.now().isoformat(), entry.entry_id, data)
    _LOGGER.info("[DIAG][%s] FINAL options for entry_id=%s: %s", datetime.now().isoformat(), entry.entry_id, options)
    if hasattr(data, 'get') and data.get('type', None) == 'buywisely':
        _LOGGER.info("[DIAG][%s] BuyWisely CONF_TARGET: %s", datetime.now().isoformat(), data.get('target', None))
    elif isinstance(data, dict) and data.get('type', None) == 'buywisely':
        _LOGGER.info("[DIAG][%s] BuyWisely CONF_TARGET: %s", datetime.now().isoformat(), data.get('target', None))

    hass.config_entries.async_update_entry(entry=entry, data=data, options=options)

    data = dict(data)
    listeners = entry.add_update_listener(options_update_listener)
    hass.data[DOMAIN][entry.entry_id] = data

    entry.async_on_unload(listeners)

    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(entity_registry, entry.entry_id)
    _LOGGER.info("[DIAG][%s] Found %d entities for entry_id=%s", datetime.now().isoformat(), len(entities), entry.entry_id)
    for e in entities:
        _LOGGER.info("[DIAG][%s] Removing entity: %s", datetime.now().isoformat(), e.entity_id)
        entity_registry.async_remove(e.entity_id)

    device_registry = dr.async_get(hass)
    devices = dr.async_entries_for_config_entry(device_registry, entry.entry_id)
    _LOGGER.info("[DIAG][%s] Found %d devices for entry_id=%s", datetime.now().isoformat(), len(devices), entry.entry_id)
    for d in devices:
        _LOGGER.info("[DIAG][%s] Removing device: %s", datetime.now().isoformat(), d.id)
        device_registry.async_update_device(d.id, remove_config_entry_id=entry.entry_id)

    _LOGGER.info("[DIAG][%s] Forwarding entry setups to platforms: %s", datetime.now().isoformat(), PLATFORMS)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _LOGGER.info("[DIAG][%s] async_setup_entry completed for entry_id=%s", datetime.now().isoformat(), entry.entry_id)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def options_update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    await hass.config_entries.async_reload(config_entry.entry_id)
