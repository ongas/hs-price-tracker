import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN

# Mock Lang class
class Lang:
    def __init__(self, hass):
        pass

    def selector(self):
        return {"lang": "en"}

# Mock price_tracker_setup_init function
def price_tracker_setup_init(hass):
    return {"lang": "en"}

class PriceTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Price Tracker config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize the config flow."""
        self.service_type = None

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.service_type = user_input["service_type"]
            return await self.async_step_product_details()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("service_type"): vol.In(["buywisely"]),
                }
            ),
        )

    async def async_step_product_details(self, user_input=None):
        """Handle the product details step."""
        if user_input is not None:
            # Create a unique ID from the URL
            unique_id = user_input["item_url"].split("id=")[-1]
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=self.service_type,
                data={"type": self.service_type},
                options={"target": [user_input]},
            )

        return self.async_show_form(
            step_id="product_details",
            data_schema=vol.Schema(
                {
                    vol.Required("item_url"): str,
                    vol.Optional("item_device_id"): str,
                    vol.Optional("item_management_category"): str,
                    vol.Optional("item_unit_type"): str,
                    vol.Optional("item_unit"): str,
                    vol.Optional("item_refresh_interval", default=30): int,
                    vol.Optional("item_price_change_interval_hour", default=24): int,
                    vol.Optional("item_debug", default=False): bool,
                    vol.Optional("proxy"): str,
                    vol.Optional("selenium"): str,
                    vol.Optional("selenium_proxy"): str,
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return PriceTrackerOptionsFlowHandler(config_entry)


class PriceTrackerOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "target",
                        default=self.config_entry.options.get("target", []),
                    ): list,
                }
            ),
        )
