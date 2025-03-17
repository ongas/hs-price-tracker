import logging
import re
import string
from typing import Optional

from curl_cffi import CurlHttpVersion

from custom_components.price_tracker.components.engine import PriceEngine
from custom_components.price_tracker.components.error import (
    InvalidItemUrlError,
    NotFoundError,
)
from custom_components.price_tracker.datas.item import ItemData, ItemStatus
from custom_components.price_tracker.services.smartstore.const import NAME, CODE
from custom_components.price_tracker.services.smartstore.parser import SmartstoreParser
from custom_components.price_tracker.utilities.safe_request import (
    SafeRequest,
    SafeRequestMethod,
)
from custom_components.price_tracker.utilities.utils import random_choice, random_bool

_LOGGER = logging.getLogger(__name__)

_URL = "https://m.{}.naver.com/{}/{}/{}"


class SmartstoreEngine(PriceEngine):
    def __init__(
            self,
            item_url: str,
            device: None = None,
            proxies: Optional[list] = None,
            selenium: Optional[str] = None,
            selenium_proxy: Optional[list] = None,
    ):
        self.item_url = item_url
        self.id = SmartstoreEngine.parse_id(item_url)
        self.store_type = self.id["store_type"]
        self.detail_type = self.id["detail_type"]
        self.store = self.id["store"]
        self.product_id = self.id["product_id"]
        self._proxies = proxies
        self._device = device
        self._selenium = selenium
        self._selenium_proxy = selenium_proxy

    async def load(self) -> ItemData | None:
        request = SafeRequest(
            proxies=self._proxies,
            version=CurlHttpVersion.V2_PRIOR_KNOWLEDGE,
            user_agents=["pc", "mobile"],
        )
        request.user_agent(user_agent="NAVER(inapp;navershopping;0;1.0.0)")

        if random_bool():
            request.cookie(
                key="NNB",
                value='PPYXCW' + ''.join(random.choices(string.ascii_uppercase, k=7))
            )
        else:
            request.cookie(
                key="NNB",
                value="PPYXCWKW"
                      + random_choice(["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "X"])
                      + random_choice(["A", "B", "C", "D", "X"])
                      + random_choice(["A", "B", "C", "D", "X"])
                      + random_choice(["A", "B", "C", "D", "E"])
                      + random_choice(["A", "B", "C", "D", "E", "F"]),
            )

        if random_bool():
            await request.request(
                method=SafeRequestMethod.GET,
                url="https://shopping.naver.com/ns/home",
                max_tries=1,
            )

        if random_bool():
            await request.request(
                method=SafeRequestMethod.GET,
                url="https://msearch.shopping.naver.com/remote_frame.html",
                max_tries=3,
            )

        request.cookie(
            key="NNB",
            value="PPYXCWKWXC"
                  + random_choice(["A", "B", "C", "D", "X"])
                  + random_choice(["A", "B", "C", "D", "E"])
                  + random_choice(["A", "B", "C", "D", "E", "F"]),
        )

        response = await request.request(
            method=SafeRequestMethod.GET,
            url=_URL.format(self.store_type, self.store, self.detail_type, self.product_id),
        )

        if response.is_not_found:
            return ItemData(
                id=self.id_str(),
                name="Deleted {}".format(self.id_str()),
                status=ItemStatus.DELETED,
                http_status=response.status_code,
            )

        if response.status_code == 429:
            _LOGGER.debug("429 Too Many Requests in NAVER")

        ## stdio out
        text = response.text

        try:
            naver_parser = SmartstoreParser(data=text)

            return ItemData(
                id=self.id_str(),
                price=naver_parser.price,
                name=naver_parser.name,
                description=naver_parser.description,
                category=naver_parser.category,
                image=naver_parser.image,
                url=naver_parser.url,
                inventory=naver_parser.inventory_status,
                delivery=naver_parser.delivery,
                options=naver_parser.options,
                status=ItemStatus.ACTIVE,
            )
        except NotFoundError as e:
            return ItemData(
                id=self.id_str(),
                name="Deleted {}".format(self.id_str()),
                status=ItemStatus.DELETED,
                http_status=response.status_code,
            )
        except Exception as e:
            raise e

    def id_str(self) -> str:
        return "{}_{}".format(self.store, self.product_id)

    @staticmethod
    def parse_id(item_url: str):
        u = re.search(
            r"(?P<store_type>smartstore|shopping|brand)\.naver\.com/(?P<store>[a-zA-Z\d\-_]+)/(?P<detail_type>products|\w+)/(?P<product_id>\d+)",
            item_url,
        )

        if u is None:
            raise InvalidItemUrlError("Bad item_url " + item_url)
        data = {}
        g = u.groupdict()
        data["store_type"] = g["store_type"]
        data["detail_type"] = g["detail_type"]
        data["store"] = g["store"]
        data["product_id"] = g["product_id"]

        return data

    @staticmethod
    def engine_code() -> str:
        return CODE

    @staticmethod
    def engine_name() -> str:
        return NAME
