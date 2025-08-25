from custom_components.price_tracker.components.setup import PriceTrackerSetup
from custom_components.price_tracker.consts.defaults import (
    CONF_URL,
    PROVIDER_BUYWISELY,
)


class BuyWiselySetup(PriceTrackerSetup):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._provider = PROVIDER_BUYWISELY

    @staticmethod
    def setup_name() -> str:
        return "BuyWisely"

    @staticmethod
    def setup_code() -> str:
        return PROVIDER_BUYWISELY

    def item_url(self, user_input: dict) -> str:
        return user_input.get(CONF_URL)