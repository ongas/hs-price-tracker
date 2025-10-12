"""The Price Tracker integration."""
from __future__ import annotations

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import entity_registry as er

from .consts.defaults import DOMAIN, PLATFORMS


_LOGGER = logging.getLogger(__name__)

async def handle_update_entity(call: ServiceCall):
    """Handle the service call to update a price tracker entity."""
    hass = call.hass
    if hass is None:
        _LOGGER.error("%s: No hass context available!", "handle_update_entity")
        return None
    _LOGGER.debug("handle_update_entity called with call.data: %s", call.data)
    entity_ids = call.data.get("entity_id")
    force_update = call.data.get("force", False)
    entity_registry = er.async_get(hass)
    if isinstance(entity_ids, str) and entity_ids.strip().upper() == "ALL":
        all_entities = entity_registry.entities
        entity_ids = [
            eid for eid in all_entities if eid.startswith(f"sensor.{DOMAIN}")
        ]
        _LOGGER.info("entity_id='ALL' provided, updating all: %s", entity_ids)
    elif entity_ids is None:
        _LOGGER.info("No entity_id provided, no update performed.")
        return None
    elif isinstance(entity_ids, str):
        entity_ids = [entity_ids]
    elif not isinstance(entity_ids, list):
        _LOGGER.warning("Invalid entity_id type: %s", type(entity_ids))
        return None
    for entity_id in entity_ids:
        _LOGGER.debug("Service call to update entity: %s (force=%s)", entity_id, force_update)
        entity_entry = entity_registry.async_get(entity_id)
        if not entity_entry:
            _LOGGER.warning("Could not find entity entry for %s in entity registry.", entity_id)
            continue
        _LOGGER.debug(
            "entity_entry for %s: %s", entity_id, entity_entry
        )
        entity_component = hass.data["entity_component"]
        _LOGGER.debug("entity_component: %s (type: %s)", entity_component, type(entity_component))
        _LOGGER.debug("entity_component[entity_entry.platform]: %s (type: %s)", entity_component[entity_entry.platform], type(entity_component[entity_entry.platform]))
        entity = entity_component[entity_entry.platform].get_entity(entity_id)
        _LOGGER.debug("Found entity object: %s (type: %s)", entity, type(entity))
        _LOGGER.debug("entity.platform: %s", entity.platform)

        if not entity:
            _LOGGER.warning("Could not find entity object for %s in entity registry.", entity_id)
            continue

        # Ensure the entity belongs to the price_tracker domain
        _LOGGER.debug("entity_entry.domain: %s", entity_entry.domain)
        if entity_entry.domain != DOMAIN:
            _LOGGER.warning(
                "Entity %s does not belong to the %s integration. Skipping update.",
                entity_id,
                DOMAIN,
            )
            continue

        _LOGGER.debug("Found entity object: %s (type: %s)", entity, type(entity))
        if hasattr(entity, "async_update"):
            _LOGGER.info(
                "Manually triggering update for %s (entity: %s, force=%s)",
                entity_id, entity, force_update
            )
            await entity.async_update(force=force_update)
        else:
            _LOGGER.warning(
                "Entity %s does not have async_update method. Entity: %s",
                entity_id, entity
            )
    return None



async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the price tracker component."""
    _LOGGER.debug("Setting up price tracker component %s", config)
    hass.data.setdefault(DOMAIN, {})
    # Initialize global configuration storage
    hass.data[DOMAIN].setdefault("global_config", {})

    # Read per-service global_excluded_domains from configuration.yaml if provided
    # Format: price_tracker: { buywisely: { global_excluded_domains: [...] } }
    domain_config = config.get(DOMAIN, {})

    # Store per-service global configurations from YAML
    for service_type, service_config in domain_config.items():
        if isinstance(service_config, dict):
            yaml_excluded_domains = service_config.get("global_excluded_domains", [])
            # Support both list format (preferred) and comma-separated string (legacy)
            if isinstance(yaml_excluded_domains, str):
                yaml_excluded_domains = [
                    d.strip() for d in yaml_excluded_domains.split(",") if d.strip()
                ]
            # Merge with any existing exclusions (from options flow)
            existing = (
                hass.data[DOMAIN]["global_config"]
                .get(service_type, {})
                .get("global_excluded_domains", [])
            )
            if isinstance(existing, str):
                existing = [d.strip() for d in existing.split(",") if d.strip()]
            merged = list(set(existing + yaml_excluded_domains))
            hass.data[DOMAIN]["global_config"][service_type] = {
                "global_excluded_domains": merged
            }
            _LOGGER.info(
                "Global excluded_domains merged for service '%s': %s",
                service_type,
                merged,
            )
    # Log full global exclusion config after YAML load
    _LOGGER.info(
        "Full global_config after YAML load: %r",
        hass.data[DOMAIN]["global_config"],
    )

    hass.services.async_register(DOMAIN, "update_entity", handle_update_entity)
    _LOGGER.info("Registered service: %s.update_entity", DOMAIN)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up price tracker from a config entry."""
    _LOGGER.info("Setting up entry: %s", entry)
    _LOGGER.info("entry.data: %s", entry.data)
    _LOGGER.info("entry.options: %s", entry.options)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault("global_config", {})
    # Store config entry data for platforms to access
    hass.data[DOMAIN][entry.entry_id] = {**entry.data, **entry.options}

    # Check if this entry has options flow global configuration that overrides YAML
    service_type = entry.data.get("service_type")
    if service_type:
        excluded_domains_key = f"global_excluded_domains_{service_type}"
        options_excluded_domains = (
            entry.options.get(excluded_domains_key, []) if entry.options else []
        )
        if isinstance(options_excluded_domains, str):
            options_excluded_domains = [
                d.strip() for d in options_excluded_domains.split(",") if d.strip()
            ]
        yaml_excluded_domains = (
            hass.data[DOMAIN]["global_config"]
            .get(service_type, {})
            .get("global_excluded_domains", [])
        )
        if isinstance(yaml_excluded_domains, str):
            yaml_excluded_domains = [
                d.strip() for d in yaml_excluded_domains.split(",") if d.strip()
            ]
        merged = list(set(yaml_excluded_domains + options_excluded_domains))
        hass.data[DOMAIN]["global_config"][service_type] = {
            "global_excluded_domains": merged
        }
        _LOGGER.info(
            "Excluded domains merged for '%s': %s",
            service_type,
            merged,
        )
    # Log full global exclusion config after merge
    _LOGGER.info(
        "Full global_config after merge: %r",
        hass.data[DOMAIN]["global_config"],
    )

    hass.services.async_register(DOMAIN, "update_entity", handle_update_entity)
    _LOGGER.info("Registered service: %s.update_entity (entry)", DOMAIN)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
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
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)
