from typing import Optional

from custom_components.price_tracker.components.engine import PriceEngine
from custom_components.price_tracker.datas.item import ItemData, ItemStatus
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
from custom_components.price_tracker.consts.confs import CONF_ITEM_URL



# Try to import crawl4ai, fallback if unavailable
import logging
try:
    from crawl4ai import AsyncWebCrawler
    from crawl4ai.extraction_strategy import NoExtractionStrategy
    _HAS_CRAWL4AI = True
except ImportError:
    AsyncWebCrawler = None
    NoExtractionStrategy = None
    _HAS_CRAWL4AI = False
    logging.getLogger(__name__).warning("[price_tracker][buywisely] crawl4ai not available, will fallback to BeautifulSoup.")

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
    ):
        self.item_url = item_url
        product_id = BuyWiselyEngine.parse_id(item_url)["product_id"]
        self.id = {"product_id": product_id, "item_url": item_url}
        self.product_id = product_id
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[DIAG][BuyWiselyEngine.__init__] item_url: {item_url}, self.id: {self.id}, self.product_id: {self.product_id}")
        self._proxies = proxies
        self._device = device
        self._selenium = selenium
        self._selenium_proxy = selenium_proxy
        self._crawler = AsyncWebCrawler(extraction_strategy=NoExtractionStrategy()) if _HAS_CRAWL4AI and AsyncWebCrawler and NoExtractionStrategy else None

    async def load(self) -> ItemData | None:
        self._request = SafeRequest()
        self._request.user_agent(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3')
        response = await self._request.request(
            method=SafeRequestMethod.GET,
            url=self.item_url,
            post_try_callables=[]
        )

        if not response.has:
            # Handle cases where request failed or no data
            return None

        html = response.text if response.text else ""

        crawl4ai_data = {}
        product_details = None
        if _HAS_CRAWL4AI and self._crawler:
            try:
                # Use only 'arun' if available, else fallback to BeautifulSoup
                if hasattr(self._crawler, 'arun'):
                    crawl_result = await self._crawler.arun(url=self.item_url)
                else:
                    logging.getLogger(__name__).warning("[price_tracker][buywisely] crawl4ai does not have a valid arun method. Falling back to BeautifulSoup.")
                    crawl_result = None
                crawl4ai_data = crawl_result if isinstance(crawl_result, dict) else {}
            except Exception as e:
                logging.getLogger(__name__).warning(f"[price_tracker][buywisely] crawl4ai extraction failed for URL: {self.item_url}. Error: {e}. Falling back to BeautifulSoup.")
                crawl4ai_data = {}
        else:
            logging.getLogger(__name__).info("[price_tracker][buywisely] crawl4ai not available, using BeautifulSoup only.")
            crawl4ai_data = {}
        product_details = parse_product(html, crawl4ai_data, product_id=self.product_id)

        price_value = product_details.get('price')
        currency_value = product_details.get('currency') or ''
        price = ItemPriceData(price=price_value, currency=currency_value) if price_value is not None and currency_value else None

        name_value = product_details.get('title') or ''
        image_value = product_details.get('image') or ''
        status_value = ItemStatus.ACTIVE if product_details.get('availability') == 'In Stock' else ItemStatus.INACTIVE

        # ItemData expects price: ItemPriceData, but None is possible. Ensure compatibility.
        return ItemData(
            id=self.product_id,
            name=name_value,
            status=status_value,
            price=price if price is not None else ItemPriceData(price=0.0, currency=""),
            url=self.item_url,
            image=image_value,
        )

    def id_str(self) -> str:
        return self.product_id

    @staticmethod
    def target_id(value: dict) -> str:
        import logging
        logger = logging.getLogger(__name__)
        item_url = value.get(CONF_ITEM_URL)
        product_id = value.get("product_id")

        logger.info(f"[DIAG][BuyWiselyEngine] target_id: value dict before entity creation: {value}")

        if not item_url:
            logger.error(f"[DIAG][BuyWiselyEngine] target_id: item_url missing or None in value: {value}")
            # If item_url is missing, we cannot generate a meaningful product_id.
            # Return a consistent invalid ID.
            return "invalid_product_id_missing_url"

        if not product_id:
            try:
                product_id = BuyWiselyEngine.parse_id(item_url)["product_id"]
            except Exception as e:
                logger.error(f"[DIAG][BuyWiselyEngine] target_id: parse_id failed for item_url={item_url}, error={e}")
                return "invalid_product_id_parse_failed"

        logger.info(f"[DIAG][BuyWiselyEngine] target_id: final product_id for entity creation: {product_id}, item_url: {item_url}")
        return product_id

    @staticmethod
    def parse_id(item_url: str):
        import logging
        import hashlib
        logger = logging.getLogger(__name__)
        # For BuyWisely, the item_url itself is the unique identifier.
        # We'll use a hash of the URL as the product_id.
        product_id = hashlib.md5(item_url.encode('utf-8')).hexdigest()
        logger.info(f"[DIAG][BuyWiselyEngine] parse_id: Generated product_id '{product_id}' from URL '{item_url}'")
        data = {"product_id": product_id}
        return data

    @staticmethod
    def engine_name() -> str:
        return NAME

    @staticmethod
    def engine_code() -> str:
        return CODE

    def url(self) -> str:
        return self.item_url