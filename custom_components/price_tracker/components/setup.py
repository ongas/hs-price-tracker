from typing import Optional
import logging
from homeassistant import config_entries
from custom_components.price_tracker.consts.confs import CONF_TYPE, CONF_TARGET

_LOGGER = logging.getLogger(__name__)

class PriceTrackerSetup:

    def _async_set_unique_id(self, user_input: Optional[dict]) -> str:
        if user_input is None or 'service_type' not in user_input:
            raise ValueError("user_input must contain 'service_type' for unique_id generation")
        return f"price-tracker-{user_input['service_type']}"

    @staticmethod
    def setup_name() -> str:
        return "Price Tracker"
    _step_setup: str = "setup"
    _config_flow: Optional[config_entries.ConfigFlow]
    _option_flow: Optional[config_entries.OptionsFlow]
    const_option_setup_select: str = "option_setup_select"
    const_option_proxy_select: str = "option_proxy_select"
    const_option_selenium_select: str = "option_selenium_select"
    const_option_personal_select: str = "option_personal_select"
    const_option_modify_select: str = "option_modify_select"
    const_option_add_select: str = "option_add_select"
    const_option_entity_select: str = "option_entity_select"
    const_option_entity_delete: str = "option_entity_delete"
    const_option_select_device: str = "service_device"
    const_option_select_entity: str = "service_entity"
    conf_target: str = "target"
    conf_proxy = "proxy"
    conf_selenium = "selenium"
    conf_selenium_proxy = "selenium_proxy"
    conf_proxy_opensource_use = "proxy_opensource"
    conf_proxy_list = "proxy_list"
    conf_item_unique_id: str = "item_unique_id"
    conf_item_device_id: str = "item_device_id"
    conf_item_url: str = "item_url"
    conf_item_management_category: str = "item_management_category"
    conf_item_unit_type: str = "item_unit_type"
    conf_item_unit: str = "item_unit"
    conf_item_refresh_interval: str = "item_refresh_interval"
    conf_item_price_change_interval_hour: str = "item_price_change_interval_hour"
    conf_item_debug: str = "item_debug"

    def __init__(self, config_flow: Optional[config_entries.ConfigFlow] = None, option_flow: Optional[config_entries.OptionsFlow] = None, config_entry=None):
        self._config_flow = config_flow
        self._option_flow = option_flow
        self._config_entry = config_entry

    async def setup(self, user_input: Optional[dict] = None):
        _LOGGER.debug("Setup(configuration): %s", user_input)
        if self._config_flow is None:
            _LOGGER.error("[PriceTrackerSetup] _config_flow is None. Cannot proceed with setup.")
            raise RuntimeError("_config_flow is None. Cannot proceed with setup.")
        if user_input is None or "product_url" not in user_input:
            # Prompt for Product URL if not provided
            import voluptuous as vol
            import homeassistant.helpers.config_validation as cv
            return self._config_flow.async_show_form(
                step_id="setup",
                data_schema=vol.Schema({
                    vol.Required("product_url"): cv.string,
                }),
                errors={},
            )
        if "service_type" not in user_input:
            _LOGGER.error("[PriceTrackerSetup] user_input missing 'service_type'. Cannot proceed with setup.")
            raise ValueError("user_input missing 'service_type'. Cannot proceed with setup.")
        await self._config_flow.async_set_unique_id(self._async_set_unique_id(user_input))
        self._config_flow._abort_if_unique_id_configured(updates={CONF_TARGET: user_input["service_type"]})
        entry_data = {**self.setup_config_data(user_input), "product_url": user_input["product_url"]}
        _LOGGER.info("[DIAG][PriceTrackerSetup] async_create_entry called with title=%s, data=%s", self.setup_name(), entry_data)
        return self._config_flow.async_create_entry(title=self.setup_name(), data=entry_data)

    def setup_config_data(self, user_input: Optional[dict] = None) -> dict:
        if user_input is None:
            return {}
        data = {CONF_TYPE: user_input["service_type"]}
        if "target" in user_input:
            data["target"] = user_input["target"]
        return data

    # ... (other methods would be similarly re-indented and fixed)