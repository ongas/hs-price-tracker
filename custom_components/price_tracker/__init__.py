from __future__ import annotations

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    device_registry as dr,
    entity_registry as er,
)

from .components.id import IdGenerator
from .consts.confs import (
    CONF_ITEM_DEVICE_ID,
    CONF_ITEM_UNIQUE_ID,
)
from .consts.defaults import DOMAIN, PLATFORMS
from .services.factory import (
    create_service_item_url_parser,
    create_service_item_target_parser,
    create_service_device_parser_and_parse,
    has_service_item_target_parser,
)
from .utilities.list import Lu


import voluptuous as vol

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the price tracker component."""
    _LOGGER.debug("Setting up price tracker component {}".format(config))
    hass.data.setdefault(DOMAIN, {})
    # Initialize global configuration storage
    hass.data[DOMAIN].setdefault("global_config", {})

    # Read per-service global_excluded_domains from configuration.yaml if provided
    # Format: price_tracker: { buywisely: { global_excluded_domains: [...] } }
    domain_config = config.get(DOMAIN, {})

    # Store per-service global configurations from YAML
    for service_type, service_config in domain_config.items():
        if isinstance(service_config, dict):
            global_excluded_domains = service_config.get("global_excluded_domains", [])
            # Support both list format (preferred) and comma-separated string (legacy)
            if isinstance(global_excluded_domains, str):
                global_excluded_domains = [d.strip() for d in global_excluded_domains.split(",") if d.strip()]
            if global_excluded_domains:
                hass.data[DOMAIN]["global_config"][service_type] = {
                    "global_excluded_domains": global_excluded_domains
                }
                _LOGGER.info(
                    "[DIAG][__init__.py] Global excluded_domains configured via YAML for service '%s': %s",
                    service_type,
                    global_excluded_domains
                )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.info("[DIAG][__init__.py] Setting up entry: %s", entry)
    _LOGGER.info("[DIAG][__init__.py] entry.data: %s", entry.data)
    _LOGGER.info("[DIAG][__init__.py] entry.options: %s", entry.options)

    # Check if this entry has options flow global configuration that overrides YAML
    service_type = entry.data.get("service_type")
    if service_type and entry.options:
        excluded_domains_key = f"global_excluded_domains_{service_type}"
        options_excluded_domains = entry.options.get(excluded_domains_key, [])
        if options_excluded_domains:
            # Options Flow takes precedence over YAML
            hass.data[DOMAIN]["global_config"][service_type] = {
                "global_excluded_domains": options_excluded_domains
            }
            _LOGGER.info(
                "[DIAG][__init__.py] Global excluded_domains configured via Options Flow for service '%s': %s (overrides YAML)",
                service_type,
                options_excluded_domains
            )

    # Define service for manual update
    SERVICE_UPDATE_ENTITY = "update_entity"
    SERVICE_SCHEMA_UPDATE_ENTITY = vol.Schema(
        {
            vol.Required("entity_id"): str,
        }
    )

    async def handle_update_entity(call):
        _LOGGER.debug(
            f"[DIAG][__init__.py] handle_update_entity called with call.data: {call.data}"
        )
        entity_id = call.data.get("entity_id")
        _LOGGER.debug(f"[DIAG][__init__.py] Service call to update entity: {entity_id}")

        entity_registry = er.async_get(hass)
        entity_entry = entity_registry.async_get(entity_id)
        _LOGGER.debug(
            f"[DIAG][__init__.py] entity_entry for {entity_id}: {entity_entry}"
        )

        # Retrieve entity from hass.data
        entity = None
        try:
            entities_dict = hass.data.get("price_tracker", {}).get("entities", {})
            _LOGGER.debug(
                f"[DIAG][__init__.py] hass.data['price_tracker']['entities'] keys at lookup: {list(entities_dict.keys())}"
            )
            entity = entities_dict.get(entity_id)
        except Exception as e:
            _LOGGER.warning(
                f"[DIAG][__init__.py] Exception while retrieving entity from hass.data: {e}"
            )

        # Fallback: try entity_component registry if not found in price_tracker dict
        if not entity:
            try:
                entity_component = hass.data.get("entity_component", {}).get("sensor")
                if entity_component and hasattr(entity_component, "get_entity"):
                    entity = entity_component.get_entity(entity_id)
                    _LOGGER.debug(
                        f"[DIAG][__init__.py] Fallback: Found entity via entity_component.get_entity: {entity}"
                    )
            except Exception as e:
                _LOGGER.warning(
                    f"[DIAG][__init__.py] Exception in fallback entity_component lookup: {e}"
                )

        if not entity:
            _LOGGER.warning(
                f"[DIAG][__init__.py] Could not find entity object for {entity_id} in hass.data['price_tracker']['entities'] or entity_component."
            )
        else:
            _LOGGER.debug(
                f"[DIAG][__init__.py] Found entity object: {entity} (type: {type(entity)})"
            )
            if hasattr(entity, "async_manual_update"):
                _LOGGER.info(
                    f"[DIAG][__init__.py] Manually triggering manual update for {entity_id} (entity: {entity})"
                )
                await entity.async_manual_update()
            elif hasattr(entity, "async_update"):
                _LOGGER.info(
                    f"[DIAG][__init__.py] Manually triggering update for {entity_id} (entity: {entity})"
                )
                await entity.async_update()
            else:
                _LOGGER.warning(
                    f"[DIAG][__init__.py] Entity {entity_id} does not have async_update/manual_update method. Entity: {entity}"
                )

    hass.services.async_register(
        DOMAIN,
        SERVICE_UPDATE_ENTITY,
        handle_update_entity,
        schema=SERVICE_SCHEMA_UPDATE_ENTITY,
    )

    # For upgrade options (1.4.0)
    if not has_service_item_target_parser(entry.data["service_type"]):
        return False

    # For upgrade options (1.0.0)
    if entry.data is not None and "device" in entry.data:
        # Update device_id safely
        def safe_device_id(x):
            device_target = create_service_device_parser_and_parse(
                entry.data["service_type"], x
            )
            return {
                **x,
                CONF_ITEM_DEVICE_ID: IdGenerator.generate_device_id(device_target)
                if device_target is not None
                else None,
            }

        data = {
            **entry.data,
            "device": Lu.map(entry.data["device"], safe_device_id),
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
                        service_type=entry.data["service_type"],
                        entity_target=create_service_item_target_parser(
                            entry.data["service_type"]
                        )(
                            create_service_item_url_parser(entry.data["service_type"])(
                                x["item_url"]
                            )
                        ),
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
        options = {"target": []}

    hass.config_entries.async_update_entry(entry=entry, data=data, options=options)

    data = dict(data)
    listeners = entry.add_update_listener(options_update_listener)
    _LOGGER.info(
        "[DIAG][__init__.py] Storing in hass.data[%s][%s]: %s",
        DOMAIN,
        entry.entry_id,
        data,
    )
    hass.data[DOMAIN][entry.entry_id] = data

    entry.async_on_unload(listeners)

    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(entity_registry, entry.entry_id)
    for e in entities:
        entity_registry.async_remove(e.entity_id)

    device_registry = dr.async_get(hass)
    devices = dr.async_entries_for_config_entry(device_registry, entry.entry_id)

    for d in devices:
        device_registry.async_update_device(d.id, remove_config_entry_id=entry.entry_id)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

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
