import logging
import re
from typing import Optional

from requests.exceptions import RequestException, Timeout # Specific exceptions for network errors

from custom_components.price_tracker.components.engine import PriceEngine
from custom_components.price_tracker.components.error import InvalidItemUrlError
from custom_components.price_tracker.consts.confs import CONF_ITEM_URL
from custom_components.price_tracker.datas.item import ItemData, ItemStatus
from custom_components.price_tracker.datas.category import ItemCategoryData
from custom_components.price_tracker.datas.price import ItemPriceData
from custom_components.price_tracker.services.buywisely.const import NAME, CODE
from custom_components.price_tracker.services.buywisely.parser import parse_product
from custom_components.price_tracker.utilities.safe_request import (
    SafeRequest,
    SafeRequestMethod,
)


_LOGGER = logging.getLogger(__name__)


class BuyWiselyEngine(PriceEngine):
    """
    Price engine for BuyWisely.com.au.
    """
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
        _LOGGER.info("[DIAG][BuyWiselyEngine.__init__] item_url: %s, self.id: %s, self.product_id: %s",
                     item_url, self.id, self.product_id)
        self._proxies = proxies
        self._device = device
        self._selenium = selenium
        self._selenium_proxy = selenium_proxy
        self._request_cls = request_cls or SafeRequest
        self._request = None # Initialize _request here

    async def load(self) -> ItemData | None:
        _LOGGER.info("[DIAG][BuyWiselyEngine.load] START.")
        self._request = self._request_cls() # Assign in load method
        await self._request.user_agent(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3')
        try:
            response = await self._request.request(
                method=SafeRequestMethod.GET,
                url=self.item_url,
                post_try_callables=[]
            )
        except (RequestException, Timeout) as e: # Catch specific network exceptions
            _LOGGER.error("Network error for item_url=%s: %s. Returning UNAVAILABLE ItemData.", self.item_url, e)
            return ItemData(
                id=self.product_id,
                name=f"Unavailable {self.product_id}",
                brand="",
                url=self.item_url,
                status=ItemStatus.INACTIVE,
                price=ItemPriceData(price=0.0, currency=""),
                image="",
                category=ItemCategoryData(None),
            )

        # Only treat as deleted if is_not_found is explicitly True
        is_not_found = getattr(response, 'is_not_found', False)
        if is_not_found is True:
            _LOGGER.warning("404/410 Not Found for item_url=%s. Returning DELETED ItemData.", self.item_url)
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

        if not response.has:
            _LOGGER.warning("No response data for item_url=%s. Returning UNAVAILABLE ItemData.", self.item_url)
            return ItemData(
                id=self.product_id,
                name=f"Unavailable {self.product_id}",
                brand="",
                url=self.item_url,
                status=ItemStatus.INACTIVE,
                price=ItemPriceData(price=0.0, currency=""),
                image="",
                category=ItemCategoryData(None),
            )

        html = response.text if response.text else ""
        # Diagnostic: Log the first 2000 characters of the fetched HTML for runtime verification
        if html:
            _LOGGER.info("[DIAG][BuyWiselyEngine.load] First 2000 chars of fetched HTML for %s:\n%s",
                         self.item_url, html[:2000])
        else:
            _LOGGER.warning("[DIAG][BuyWiselyEngine.load] No HTML content fetched for %s", self.item_url)
        product_details = await parse_product(html, product_id=self.product_id, item_url=self.item_url)

        # Validate that the extracted price is greater than zero
        if product_details and product_details.price and product_details.price.price <= 0.0:
            _LOGGER.error("Extracted price for item_url=%s is zero or less. This indicates an extraction bug.", self.item_url)
            raise ValueError("Extracted price cannot be zero or less.")

        # Ensure return type is always ItemData
        if isinstance(product_details, dict):
            # Defensive: fallback if parse_product returns dict (shouldn't in prod)
            return ItemData(
                id=product_details.get('id', self.product_id),
                name=product_details.get('name', 'UNKNOWN'),
                brand=product_details.get('brand', ''),
                url=product_details.get('url', self.item_url),
                status=product_details.get('status', ItemStatus.ACTIVE),
                price=product_details.get('price', ItemPriceData(price=0.0, currency="")),
                image=product_details.get('image', ''),
                category=product_details.get('category', ItemCategoryData(None)),
            )
        return product_details

    def id_str(self) -> str:
        """Returns the product ID as a string."""
        return self.product_id

    @staticmethod
    def target_id(value: dict) -> str:
        """
        Extracts the product ID from the configuration value.
        """
        logger = logging.getLogger(__name__)
        item_url = value.get(CONF_ITEM_URL) if value else None
        product_id = value.get("product_id") if value else None
        logger.info("[DIAG][BuyWiselyEngine] target_id: value dict before entity creation: %s", value)
        if not item_url:
            logger.error("[DIAG][BuyWiselyEngine] target_id: item_url missing or None in value: %s", value)
            return "invalid_product_id"
        if not product_id:
            try:
                product_id = BuyWiselyEngine.parse_id(item_url)["product_id"]
            except InvalidItemUrlError as e: # Catch specific error
                logger.error("[DIAG][BuyWiselyEngine] target_id: parse_id failed for item_url=%s, error=%s",
                             item_url, e)
                return "invalid_product_id"
            except Exception as e: # Catch any other unexpected errors
                logger.error("[DIAG][BuyWiselyEngine] target_id: unexpected error during parse_id for item_url=%s, error=%s",
                             item_url, e)
                return "invalid_product_id"
        logger.info("[DIAG][BuyWiselyEngine] target_id: final product_id for entity creation: %s, item_url: %s",
                     product_id, item_url)
        return product_id

    @staticmethod
    def parse_id(item_url: str) -> dict:
        """
        Parses the item URL to extract the product ID.
        Raises InvalidItemUrlError if the URL is not valid.
        """
        logger = logging.getLogger(__name__)
        # Validate domain
        if "buywisely.com.au" not in item_url:
            logger.error("[DIAG][BuyWiselyEngine] parse_id: Invalid domain in item_url %s", item_url)
            raise InvalidItemUrlError("Invalid domain in item_url " + item_url)

        # Extract product name after '/product/'
        u = re.search(r'/product/([^/?#]+)', item_url)
        if u is None:
            logger.error("[DIAG][BuyWiselyEngine] parse_id: Bad item_url %s", item_url)
            raise InvalidItemUrlError("Bad item_url " + item_url)
        product_name = u.group(1)
        logger.info("[DIAG][BuyWiselyEngine] parse_id: Extracted product_name '%s' from URL '%s'",
                     product_name, item_url)
        data = {"product_id": product_name}
        return data

    @staticmethod
    def engine_name() -> str:
        """Returns the name of the engine."""
        return NAME

    @staticmethod
    def engine_code() -> str:
        """Returns the code of the engine."""
        return CODE

    def url(self) -> str:
        """Returns the item URL."""
        return self.item_url