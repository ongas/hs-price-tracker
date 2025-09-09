import logging
from typing import Any, Dict, Optional

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback, HomeAssistant

from custom_components.price_tracker.utilities.list import Lu
from .components.setup import PriceTrackerSetup
from .consts.confs import CONF_TYPE
from .consts.defaults import DOMAIN
from .services.setup import (
    price_tracker_setup_option_service,
)

_LOGGER = logging.getLogger(__name__)


class PriceTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    data: Optional[Dict[str, Any]]

    async def async_step_reconfigure(self, user_input: dict = None):
        pass

    async def async_migrate_entry(
        self, hass: HomeAssistant, config_entry: ConfigEntry
    ) -> bool:
        """Migrate old entry."""
        _LOGGER.debug("Migrate entry (config-flow)")

        return False

    async def async_step_import(self, import_info):
        return await self.async_step_user(import_info)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return PriceTrackerOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        errors = {}
        if not user_input or "service_type" not in user_input:
            # First step: select service
            import voluptuous as vol
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema({
                    vol.Required("service_type"): vol.In(price_tracker_service_types()),
                }),
                errors=errors,
            )
        # Second step: prompt for product_url
        # Store using CONF_TYPE key for consistency
        self.service_type = user_input["service_type"]
        self._service_type_key = CONF_TYPE
        return await self.async_step_product_url()

    async def async_step_product_url(self, user_input=None):
        errors = {}
        if not user_input or "product_url" not in user_input:
            import voluptuous as vol
            return self.async_show_form(
                step_id="product_url",
                data_schema=vol.Schema({
                    vol.Required("product_url"): str,
                }),
                errors=errors,
            )
        # All required fields present, create the entry
        # Use CONF_TYPE for service type key
        # Ensure both canonical 'type' key and 'product_url' are present in entry data
        entry_data = {self._service_type_key: self.service_type, "product_url": user_input["product_url"]}
        # Only include 'lang' if present in user_input
        if 'lang' in user_input:
            entry_data['lang'] = user_input['lang']
        return self.async_create_entry(
            title="Price Tracker",
            data=entry_data,
        )
def price_tracker_service_types():
    # Return the list of available service types (e.g., Buywisely, Coupang, etc.)
    from custom_components.price_tracker.services.setup import _KIND
    return _KIND


class PriceTrackerOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry) -> None:
        self.config_entry = config_entry
        self.setup: Optional[PriceTrackerSetup] = price_tracker_setup_option_service(
            service_type=self.config_entry.data[CONF_TYPE],
            option_flow=self,
            config_entry=config_entry,
        )

    async def async_step_init(self, user_input: dict = None):
        """Delegate step"""
        if self.setup is None:
            return self.async_show_form(
                step_id="init",
                errors={"base": "setup_not_found"},
            )
        return await self.setup.setup(user_input)

    async def async_step_setup(self, user_input=None):
        """Set-up flows."""
        if self.setup is None:
            return self.async_show_form(
                step_id="setup",
                errors={"base": "setup_not_found"},
            )
        if user_input is None:
            return await self.setup.setup(user_input)
        # Proxy configuration and other options would be handled here if implemented
        # For now, fallback to setup
        return await self.setup.setup(user_input)

        # Selenium select
        if (
            self.setup.const_option_setup_select in user_input
            and user_input[self.setup.const_option_setup_select]
            == self.setup.const_option_selenium_select
        ):
            return await self.setup.option_selenium(user_input)

        # 1
        if self.setup.const_option_setup_select in user_input:
            if self.setup.const_option_select_device not in user_input:
                device = await self.setup.option_select_device(user_input)
                if device is not None:
                    return device

        if (
            Lu.get(user_input, self.setup.const_option_setup_select)
            == self.setup.const_option_modify_select
            and Lu.get(user_input, self.setup.const_option_select_entity) is None
        ):
            return await self.setup.option_select_entity(
                device=Lu.get(user_input, self.setup.const_option_select_device),
                user_input=user_input,
            )

        # 2
        if self.setup.const_option_setup_select in user_input:
            if (
                user_input[self.setup.const_option_setup_select]
                == self.setup.const_option_modify_select
            ):
                return await self.setup.option_modify(
                    device=Lu.get(user_input, self.setup.const_option_select_device),
                    entity=Lu.get(user_input, self.setup.const_option_select_entity),
                    user_input=user_input,
                )
            elif (
                user_input[self.setup.const_option_setup_select]
                == self.setup.const_option_add_select
            ):
                return await self.setup.option_upsert(
                    device=Lu.get(user_input, self.setup.const_option_select_device),
                    user_input=user_input,
                )

        raise NotImplementedError("Not implemented (Set up). {}".format(user_input))
