import json
import aiohttp
from .parser import parse_product
from homeassistant.const import CONF_URL
from custom_components.price_tracker.utilities.safe_request import SafeRequest, SafeRequestMethod
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import NoExtractionStrategy

class BuyWiselyEngine:
    crawl4ai_compatible = True
    def __init__(self, extraction_method: str = "basic"):
        self._request = SafeRequest()
        self._extraction_method = extraction_method
        self._crawler = AsyncWebCrawler(extraction_strategy=NoExtractionStrategy())

    @staticmethod
    def engine_code() -> str:
        return "buywisely"

    @staticmethod
    def parse_id(config: dict) -> str | None:
        return config.get(CONF_URL)

    @staticmethod
    def target_id(config: dict) -> str | None:
        return config.get(CONF_URL)

    async def get_product_details(self, url: str, product_id: str | None = None) -> dict:
        self._request.user_agent(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3')
        response = await self._request.request(
            method=SafeRequestMethod.GET,
            url=url,
            post_try_callables=[]
        )

        if not response.has:
            return {}

        html = response.text if response.text else ""
        crawl4ai_data = {}
        if self._extraction_method == "advanced":
            try:
                async with self._crawler:
                    crawl_result = await self._crawler.arun(url=url)
                    crawl4ai_data = crawl_result if isinstance(crawl_result, dict) else {}
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(
                    f"[price_tracker][buywisely] Advanced crawl4ai extraction failed for URL: {url}. "
                    f"Error: {e}\n"
                    "This usually means Playwright browser binaries are missing or not installed. "
                    "Run 'playwright install' in your environment to resolve. Falling back to basic extraction."
                )
        product_details = parse_product(html, crawl4ai_data, product_id=product_id)
        return product_details
