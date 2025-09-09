import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback, HomeAssistant

from custom_components.price_tracker.utilities.list import Lu
from custom_components.price_tracker.components.lang import Lang
from .components.error import UnsupportedError
from .components.setup import PriceTrackerSetup
from .consts.defaults import DOMAIN
from .services.setup import (
    price_tracker_setup_service,
    price_tracker_setup_service_user_input,
    price_tracker_setup_init,
    price_tracker_setup_option_service,
    _SERVICE_TYPE,
)

_LOGGER = logging.getLogger(__name__)


class PriceTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    def __init__(self) -> None:
        super().__init__()
        self._data: dict[str, Any] = {}
    

    
    

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

    async def async_step_service_selection(self, user_input=None):
        errors: dict = {}

        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_user()
        else:
            pass

        return self.async_show_form(
            step_id="service_selection",
            data_schema=price_tracker_setup_init(self.hass),
            errors=errors,
        )

    async def async_step_user(self, user_input=None):
        errors: dict = {}

        service_type = self._data.get(_SERVICE_TYPE)

        # If service_type is not yet selected, go to service selection step
        if service_type is None:
            return await self.async_step_service_selection()

        dynamic_schema_dict = {}
        if service_type == "buywisely":
            dynamic_schema_dict["product_url"] = str # vol.Required will be added when creating the final schema

        data_schema = vol.Schema({
            **dynamic_schema_dict,
            **Lang(self.hass).selector(),
        })

        if user_input is not None:
            combined_input = {**self._data, **user_input}
            try:
                if step := price_tracker_setup_service(
                    service_type=price_tracker_setup_service_user_input(combined_input),
                    config_flow=self,
                ):
                    return await step.setup(combined_input)
            except UnsupportedError:
                errors["base"] = "unsupported"
            except vol.Invalid as err:
                if hasattr(err, 'errors'):
                    for error in err.errors:
                        if error.path and str(error.path[0]) == "product_url" and service_type == "buywisely":
                            errors["product_url"] = "required"
                        elif error.path and len(error.path) > 0:
                            errors[str(error.path[0])] = "required"
                        else:
                            errors["base"] = "invalid_input"
                else:
                    # Handle direct vol.Invalid exceptions (e.g., from setup.py)
                    errors["base"] = str(err) # Use the exception message directly
                _LOGGER.debug("Validation error: %s", err)
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors
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
            service_type=self.config_entry.data[_SERVICE_TYPE],
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