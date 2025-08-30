import re
from typing import Optional

from custom_components.price_tracker.components.engine import PriceEngine
from custom_components.price_tracker.components.error import (
    InvalidItemUrlError,
)
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
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import NoExtractionStrategy

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
        self.id = BuyWiselyEngine.parse_id(item_url)
        self.product_id = self.id["product_id"]
        self._proxies = proxies
        self._device = device
        self._selenium = selenium
        self._selenium_proxy = selenium_proxy
        self._crawler = AsyncWebCrawler(extraction_strategy=NoExtractionStrategy())

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
        try:
            async with self._crawler:
                crawl_result = await self._crawler.arun(url=self.item_url)
                crawl4ai_data = crawl_result if isinstance(crawl_result, dict) else {}
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(
                f"[price_tracker][buywisely] Advanced crawl4ai extraction failed for URL: {self.item_url}. "
                f"Error: {e}\n"
                "This usually means Playwright browser binaries are missing or not installed. "
                "Run 'playwright install' in your environment to resolve. Falling back to basic extraction."
            )
        product_details = parse_product(html, crawl4ai_data, product_id=self.product_id)
        
        price_value = product_details.get('price')
        price = ItemPriceData(price=price_value, currency=product_details.get('currency')) if price_value is not None else None

        return ItemData(
            id=self.product_id,
            name=product_details.get('title'),
            status=ItemStatus.ACTIVE if product_details.get('availability') == 'In Stock' else ItemStatus.INACTIVE,
            price=price,
            url=self.item_url,
            image=product_details.get('image'),
        )

    def id_str(self) -> str:
        return self.product_id

    @staticmethod
    def target_id(item_url: str):
        return BuyWiselyEngine.parse_id(item_url)["product_id"]

    @staticmethod
    def parse_id(item_url: str):
        u = re.search(r'id=(?P<product_id>\d+)', item_url)
        if u is None:
            raise InvalidItemUrlError("Bad item_url " + item_url)
        data = {}
        g = u.groupdict()
        data["product_id"] = g["product_id"]
        return data

    @staticmethod
    def engine_name() -> str:
        return NAME

    @staticmethod
    def engine_code() -> str:
        return CODE

    def url(self) -> str:
        return _ITEM_LINK.format(self.product_id)