import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback, HomeAssistant

from custom_components.price_tracker.utilities.list import Lu
from custom_components.price_tracker.components.lang import Lang
from .components.error import UnsupportedError
# Import voluptuous at the top so it is always available
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
    

    
    

    async def async_step_reconfigure(self, user_input = None):
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
            # Add product_url and refresh_interval_minutes to the schema for BuyWisely
            dynamic_schema_dict["product_url"] = str
            # Use a user-friendly label and show unit for refresh interval by changing the key
            # For future: use translations for label if needed
            dynamic_schema_dict[vol.Required(
                "refresh_interval_minutes",
                default=30,
            )] = vol.All(
                int,
                vol.Range(min=1),
            )

        data_schema = vol.Schema({
            **dynamic_schema_dict,
            **Lang(self.hass).selector(),
        })

        if user_input is not None:
            combined_input = {**self._data, **user_input}
            try:
                service_type_val = price_tracker_setup_service_user_input(combined_input)
                if service_type_val is not None:
                    step = price_tracker_setup_service(
                        service_type=service_type_val,
                        config_flow=self,
                    )
                    if step:
                        return await step.setup(combined_input)
            except UnsupportedError:
                errors["base"] = "unsupported"
            except vol.Invalid as err:
                # Try to extract error details if available
                error_list = getattr(err, 'errors', None)
                if error_list:
                    for error in error_list:
                        if getattr(error, 'path', None) and str(error.path[0]) == "product_url" and service_type == "buywisely":
                            errors["product_url"] = "required"
                        elif getattr(error, 'path', None) and len(error.path) > 0:
                            errors[str(error.path[0])] = "required"
                        else:
                            errors["base"] = "invalid_input"
                else:
                    errors["base"] = str(err)
                _LOGGER.debug("Validation error: %s", err)
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            if user_input is not None:
                # Map refresh_interval_minutes to refresh_interval for internal logic
                mapped_input = dict(user_input)
                if "refresh_interval_minutes" in mapped_input:
                    mapped_input["refresh_interval"] = mapped_input["refresh_interval_minutes"]
                combined_input = {**self._data, **mapped_input}
                try:
                    service_type_val = price_tracker_setup_service_user_input(combined_input)
                    if service_type_val is not None:
                        step = price_tracker_setup_service(
                            service_type=service_type_val,
                            config_flow=self,
                        )
                        if step:
                            return await step.setup(combined_input)
                except UnsupportedError:
                    errors["base"] = "unsupported"
                except vol.Invalid as err:
                    # Try to extract error details if available
                    error_list = getattr(err, 'errors', None)
                    if error_list:
                        for error in error_list:
                            if getattr(error, 'path', None) and str(error.path[0]) == "product_url" and service_type == "buywisely":
                                errors["product_url"] = "required"
                            elif getattr(error, 'path', None) and str(error.path[0]) == "refresh_interval_minutes" and service_type == "buywisely":
                                errors["refresh_interval_minutes"] = "required"
                            elif getattr(error, 'path', None) and len(error.path) > 0:
                                errors[str(error.path[0])] = "required"
                            else:
                                errors["base"] = "invalid_input"
                    else:
                        errors["base"] = str(err)
                    _LOGGER.debug("Validation error: %s", err)
                except Exception:
                    _LOGGER.exception("Unexpected exception")
                    errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors
        )

    async def async_step_setup(self, user_input = None):
        if user_input is None:
            user_input = {}
        service_type_val = price_tracker_setup_service_user_input(user_input)
        if service_type_val is not None:
            step = price_tracker_setup_service(
                service_type=service_type_val,
                config_flow=self,
            )
            if step:
                return await step.setup(user_input)
        raise NotImplementedError("Not implemented (Set up). {}".format(user_input))


class PriceTrackerOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry) -> None:
        self.config_entry = config_entry
        service_type = self.config_entry.data.get(_SERVICE_TYPE) if self.config_entry and self.config_entry.data else None
        if service_type is not None:
            self.setup = price_tracker_setup_option_service(
                service_type=service_type,
                option_flow=self,
                config_entry=config_entry,
            )
        else:
            self.setup = None
        if self.setup is None:
            _LOGGER.error("Failed to initialize PriceTrackerSetup in OptionsFlowHandler. service_type: %s", service_type)
            # Optionally, raise or handle gracefully

    async def async_step_init(self, user_input = None):
        """Delegate step"""
        if user_input is None:
            user_input = {}
        return await self.setup.option_setup(user_input)

    async def async_step_setup(self, user_input = None):
        """Set-up flows."""
        if user_input is None:
            user_input = {}

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