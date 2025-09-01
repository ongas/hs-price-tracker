import logging
from typing import Any, Dict, Optional

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback, HomeAssistant

from custom_components.price_tracker.utilities.list import Lu
from .components.error import UnsupportedError
from .components.setup import PriceTrackerSetup
from .consts.confs import CONF_TYPE
from .consts.defaults import DOMAIN
from .services.setup import (
    price_tracker_setup_service,
    price_tracker_setup_service_user_input,
    price_tracker_setup_init,
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
        errors: dict = {}

        if user_input is None:
            # Step 1: Select service and language
            return self.async_show_form(
                step_id="user",
                data_schema=price_tracker_setup_init(self.hass),
                errors=errors,
            )

        # Step 2: Prompt for product details after service selection
        self.selected_service_type = user_input.get("service_type")
        self.selected_lang = user_input.get("lang")

        # Show product details form
        return await self.async_step_product_details()

    async def async_step_product_details(self, user_input=None):
        errors: dict = {}
        import voluptuous as vol
        # Basic required field
        schema = vol.Schema({
            vol.Required("item_url"): str,
            vol.Optional("show_advanced", default=False): bool,
        })

        # Advanced fields schema
        advanced_schema = vol.Schema({
            vol.Optional("item_device_id", default=""): str,
            vol.Optional("item_management_category", default=""): str,
            vol.Optional("item_unit_type", default="auto"): str,
            vol.Optional("item_unit", default=""): str,
            vol.Optional("item_refresh_interval", default=30): int,
            vol.Optional("item_price_change_interval_hour", default=24): int,
            vol.Optional("item_debug", default=False): bool,
            vol.Optional("proxy", default=""): str,
            vol.Optional("selenium", default=""): str,
            vol.Optional("selenium_proxy", default=""): str,
        })

        # Diagnostic: print user_input for debugging
        import logging
        logging.getLogger(__name__).info(f"[price_tracker][config_flow] user_input: {user_input}")

        # Step 1: Show basic form if no input or not advanced
        if user_input is None:
            return self.async_show_form(
                step_id="product_details",
                data_schema=schema,
                errors=errors,
                description_placeholders={"advanced": "Expand for more options"},
            )

        # Step 2: If advanced requested, show advanced form
        if user_input.get("show_advanced", False) and len(user_input) == 1:
            # Only 'show_advanced' checked, re-render with advanced fields
            return self.async_show_form(
                step_id="product_details",
                data_schema=vol.Schema({
                    vol.Required("item_url"): str,
                    vol.Optional("show_advanced", default=True): bool,
                    **advanced_schema.schema,
                }),
                errors=errors,
            )

        # Step 3: Submission: must have item_url and (optionally) advanced fields
        item_url = user_input.get("item_url", "")
        import re
        match = re.search(r"id=(?P<product_id>\d+)", item_url)
        item_unique_id = match.group("product_id") if match else ""

        config_data = {
            "service_type": getattr(self, "selected_service_type", "buywisely"),
            "lang": getattr(self, "selected_lang", "en"),
            "item_url": item_url,
            "item_unique_id": item_unique_id,
        }
        for key in advanced_schema.schema.keys():
            if key in user_input:
                config_data[key] = user_input[key]

        # Diagnostic: print config_data for debugging
        logging.getLogger(__name__).info(f"[price_tracker][config_flow] config_data: {config_data}")

        # Setup entry with all config data
        if step := price_tracker_setup_service(
            service_type=config_data["service_type"],
            config_flow=self,
        ):
            return await step.setup(config_data)

        errors["base"] = "unsupported"
        return self.async_show_form(
            step_id="product_details",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_setup(self, user_input=None):
        if step := price_tracker_setup_service(
            service_type=price_tracker_setup_service_user_input(user_input),
            config_flow=self,
        ):
            return await step.setup(user_input)

        raise NotImplementedError("Not implemented (Set up). {}".format(user_input))


class PriceTrackerOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry) -> None:
        self.config_entry = config_entry
        self.setup: PriceTrackerSetup = price_tracker_setup_option_service(
            service_type=self.config_entry.data[CONF_TYPE],
            option_flow=self,
            config_entry=config_entry,
        )

    async def async_step_init(self, user_input: dict = None) -> dict:
        """Delegate step"""
        return await self.setup.option_setup(user_input)

    async def async_step_setup(self, user_input: dict = None):
        """Set-up flows."""

        # Select option (1)
        if user_input is None:
            return await self.setup.option_setup(user_input)

        # Proxy configuration
        if (
            self.setup.const_option_setup_select in user_input
            and user_input[self.setup.const_option_setup_select]
            == self.setup.const_option_proxy_select
        ):
            return await self.setup.option_proxy(user_input)

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
