from custom_components.price_tracker.components.setup import PriceTrackerSetup
from custom_components.price_tracker.services.buywisely.const import CODE, NAME


class BuyWiselySetup(PriceTrackerSetup):
    """Buywisely service setup."""

    @staticmethod
    def setup_code() -> str:
        return CODE

    @staticmethod
    def setup_name() -> str:
        return NAME

    def item_url(self, user_input: dict) -> str:
        return user_input.get("url", "")
