import re
from typing import Optional

from custom_components.price_tracker.components.engine import PriceEngine
from custom_components.price_tracker.components.error import (
    InvalidItemUrlError,
)
from custom_components.price_tracker.datas.item import ItemData, ItemStatus
from custom_components.price_tracker.datas.category import ItemCategoryData
from custom_components.price_tracker.datas.price import ItemPriceData
from custom_components.price_tracker.services.buywisely.const import (
    NAME,
    CODE,
)
from custom_components.price_tracker.services.buywisely.parser import parse_product
from custom_components.price_tracker.utilities.safe_request import (
    SafeRequest,
    SafeRequestMethod,
)


import logging
_LOGGER = logging.getLogger(__name__)

_URL = "https://www.buywisely.com.au/item/show?id={}"
_ITEM_LINK = "https://www.buywisely.com.au/item/show?id={}"


class BuyWiselyEngine(PriceEngine):
    def __init__(
            self,
            item_url: str,
            device: None = None,
            proxies: Optional[list] = None,
            selenium: Optional[str] = None,
            selenium_proxy: Optional[list] = None,
            request_cls=None,
        ):
        self.item_url = item_url
        product_id = BuyWiselyEngine.parse_id(item_url)["product_id"]
        self.id = {"product_id": product_id, "item_url": item_url}
        self.product_id = product_id
        _LOGGER.info(f"[DIAG][BuyWiselyEngine.__init__] item_url: {item_url}, self.id: {self.id}, self.product_id: {self.product_id}")
        self._proxies = proxies
        self._device = device
        self._selenium = selenium
        self._selenium_proxy = selenium_proxy
        
        self._request_cls = request_cls or SafeRequest

    async def load(self) -> ItemData | None:
        self._request = self._request_cls()
        self._request.user_agent(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3')
        response = await self._request.request(
            method=SafeRequestMethod.GET,
            url=self.item_url,
            post_try_callables=[]
        )

        if not response.has:
            _LOGGER.warning(f"No response data for item_url={self.item_url}. Returning DELETED ItemData.")
            return ItemData(
                id=self.product_id,
                name=f"Deleted {self.product_id}",
                brand="",
                url=self.item_url,
                status=ItemStatus.DELETED,
                price=ItemPriceData(price=0.0, currency=""),
                image="",
                category=ItemCategoryData(None),
            )

        html = response.text if response.text else ""
        product_details = parse_product(html, product_id=self.product_id, item_url=self.item_url)
        
        return product_details

    def id_str(self) -> str:
        return self.product_id

    @staticmethod
    def target_id(value: dict) -> str:
        from custom_components.price_tracker.consts.confs import CONF_ITEM_URL
        import logging
        logger = logging.getLogger(__name__)
        item_url = value.get(CONF_ITEM_URL) if value else None
        product_id = value.get("product_id") if value else None
        logger.info(f"[DIAG][BuyWiselyEngine] target_id: value dict before entity creation: {value}")
        if not item_url:
            logger.error(f"[DIAG][BuyWiselyEngine] target_id: item_url missing or None in value: {value}")
            return "invalid_product_id"
        if not product_id:
            try:
                product_id = BuyWiselyEngine.parse_id(item_url)["product_id"]
            except Exception as e:
                logger.error(f"[DIAG][BuyWiselyEngine] target_id: parse_id failed for item_url={item_url}, error={e}")
                return "invalid_product_id"
        logger.info(f"[DIAG][BuyWiselyEngine] target_id: final product_id for entity creation: {product_id}, item_url: {item_url}")
        return product_id

    @staticmethod
    def parse_id(item_url: str):
        import logging
        logger = logging.getLogger(__name__)
        # Extract product name after '/product/'
        u = re.search(r'/product/([^/?#]+)', item_url)
        if u is None:
            logger.error(f"[DIAG][BuyWiselyEngine] parse_id: Bad item_url {item_url}")
            raise InvalidItemUrlError("Bad item_url " + item_url)
        product_name = u.group(1)
        logger.info(f"[DIAG][BuyWiselyEngine] parse_id: Extracted product_name '{product_name}' from URL '{item_url}'")
        data = {"product_id": product_name}
        return data

    @staticmethod
    def engine_name() -> str:
        return NAME

    @staticmethod
    def engine_code() -> str:
        return CODE

    def url(self) -> str:
        return self.item_url