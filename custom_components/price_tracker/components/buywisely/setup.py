
from typing import Optional
from ..setup import PriceTrackerSetup
from .const import CODE, NAME

class BuyWiselySetup(PriceTrackerSetup):
    """Buywisely service setup."""

    @staticmethod
    def setup_code() -> str:
        return CODE

    @staticmethod
    def setup_name() -> str:
        return NAME


    def setup_config_data(self, user_input: Optional[dict] = None) -> dict:
        # Collect all relevant config fields for Buywisely
        config = {}
        if user_input is None:
            return config
        # Standard fields
        config["type"] = user_input.get("service_type", "buywisely")
        config["item_url"] = user_input.get("item_url", "")
        config["item_unique_id"] = user_input.get("item_unique_id", "")
        config["item_device_id"] = user_input.get("item_device_id", "")
        config["item_management_category"] = user_input.get("item_management_category", "")
        config["item_unit_type"] = user_input.get("item_unit_type", "")
        config["item_unit"] = user_input.get("item_unit", "")
        config["item_refresh_interval"] = user_input.get("item_refresh_interval", "")
        config["item_price_change_interval_hour"] = user_input.get("item_price_change_interval_hour", "")
        config["item_debug"] = user_input.get("item_debug", False)
        # Device/proxy/selenium options if present
        config["device"] = user_input.get("service_device", "")
        config["proxy"] = user_input.get("proxy", "")
        config["selenium"] = user_input.get("selenium", "")
        config["selenium_proxy"] = user_input.get("selenium_proxy", "")
        return config
