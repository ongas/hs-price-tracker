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


# Try to import crawl4ai, fallback if unavailable
import logging
_LOGGER = logging.getLogger(__name__)
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
        _LOGGER.info(f"[DIAG][BuyWiselyEngine.__init__] item_url: {item_url}, self.id: {self.id}, self.product_id: {self.product_id}")
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

        import logging
        logger = logging.getLogger(__name__)

        if not response.has:
            # Handle cases where request failed or no data
            logger.warning(f"[DIAG][BuyWiselyEngine.load] No response data for item_url={self.item_url}. Returning DELETED ItemData.")
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
        logger.info('[DIAG][BuyWiselyEngine.load] HTML snapshot: %s', html)

        crawl4ai_data = {}
        product_details = None
        if _HAS_CRAWL4AI and self._crawler:
            try:
                logger.info(f"[DIAG][BuyWiselyEngine.load] item_url: {self.item_url}, self.id: {self.id}, self.product_id: {self.product_id}")
                if hasattr(self._crawler, 'arun'):
                    crawl_result = await self._crawler.arun(url=self.item_url)
                    if not isinstance(crawl_result, dict):
                        logger.warning(f"[price_tracker][buywisely] crawl4ai returned non-dict result, falling back to BeautifulSoup.")
                        crawl4ai_data = {}
                    else:
                        crawl4ai_data = crawl_result
                else:
                    logger.warning(f"[price_tracker][buywisely] crawl4ai does not have a valid arun method. Falling back to BeautifulSoup.")
                    crawl4ai_data = {}
            except Exception as e:
                logger.warning(f"[price_tracker][buywisely] crawl4ai extraction failed for URL: {self.item_url}. Error: {e}. Falling back to BeautifulSoup.")
                crawl4ai_data = {}
        else:
            logger.info("[price_tracker][buywisely] crawl4ai not available, using BeautifulSoup only.")
            crawl4ai_data = {}

        product_details = parse_product(html, crawl4ai_data, product_id=self.product_id)

        price_value = product_details.get('price')
        currency_value = product_details.get('currency') or ''
        brand_value = product_details.get('brand') or ''
        product_link_value = product_details.get('product_link') or ''
        logger.info(f"[DIAG][BuyWiselyEngine.load] Extracted price_value: {price_value}, currency_value: {currency_value}, brand: {brand_value}, product_link: {product_link_value}, product_details: {product_details}")
        price = ItemPriceData(price=price_value, currency=currency_value) if price_value is not None and currency_value else ItemPriceData(price=0.0, currency="")

        name_value = product_details.get('title') or ''
        image_value = product_details.get('image') or ''
        status_value = ItemStatus.ACTIVE if product_details.get('availability') == 'In Stock' else ItemStatus.INACTIVE
        logger.info(f"[DIAG][BuyWiselyEngine.load] ItemData fields: id={self.product_id}, name={name_value}, brand={brand_value}, product_link={product_link_value}, status={status_value}, price={price}, url={self.item_url}, image={image_value}")

        result = ItemData(
            id=self.product_id,
            name=name_value,
            brand=brand_value,
            url=product_link_value if product_link_value else self.item_url,
            status=status_value,
            price=price,
            image=image_value,
            category=ItemCategoryData(None),
        )
        logger.info(f"[DIAG][BuyWiselyEngine.load] Returning ItemData: {result}, as_dict: {getattr(result, 'dict', 'no dict') if hasattr(result, 'dict') else str(result)}")
        return result

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