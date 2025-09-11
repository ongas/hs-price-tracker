import asyncio
import json
import logging
import random
from enum import Enum
from typing import Optional, Callable, Self, Awaitable
import dataclasses

import fake_useragent
from curl_cffi import requests, CurlHttpVersion, CurlSslVersion

_LOGGER = logging.getLogger(__name__)

@dataclasses.dataclass
class SafeRequestResponseData:
    data: Optional[str] = None
    status_code: int = 400
    access_token: Optional[str] = None
    cookies: dict = dataclasses.field(default_factory=dict)

    @property
    def text(self):
        return self.data

    @property
    def has(self):
        return (
            self.status_code is not None
            and self.status_code <= 399
            and self.data is not None
            and self.data != ""
        )

class SafeRequestMethod(Enum):
    POST = "post"
    GET = "get"
    PUT = "put"
    DELETE = "delete"

class SafeRequest:
    def __init__(
        self,
        impersonate: str = "chrome124",
        version: Optional[CurlHttpVersion] = CurlHttpVersion.V2TLS,
    ):
        self._headers = {
            "Accept": "text/html,application/json,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9,ko;q=0.8,ja;q=0.7,zh-CN;q=0.6,zh;q=0.5",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Pragma": "no-cache",
        }
        self._timeout = 25
        self._impersonate = impersonate
        self._version = version
        self._cookies = {}

    def user_agent(
        self,
        user_agent: Optional[str] | list = None,
        mobile_random: bool = False,
        pc_random: bool = False,
    ):
        if user_agent is not None:
            if isinstance(user_agent, list):
                self._headers["User-Agent"] = random.choice(user_agent)
            else:
                self._headers["User-Agent"] = user_agent
            return self

        if mobile_random or pc_random:
            ua_engine = fake_useragent.UserAgent(platforms=(["mobile"] if mobile_random else []) + (["pc"] if pc_random else []))
            self._headers["User-Agent"] = ua_engine.random

        return self

    async def request(
        self,
        url: str,
        method: SafeRequestMethod = SafeRequestMethod.GET,
        data: any = None,
        timeout: int = 25,
        raise_errors: bool = False,
        max_tries: int = 1,
        post_try_callables: list[Callable[[Self], Awaitable[None]]] = None,
        retain_cookie=True,
    ) -> SafeRequestResponseData:
        async with requests.AsyncSession(
            impersonate=self._impersonate, http_version=self._version
        ) as session:
            try:
                response = await session.request(
                    method=method.name.upper(),
                    url=url,
                    headers=self._headers,
                    json=data if method in [SafeRequestMethod.POST, SafeRequestMethod.PUT] else None,
                    data=data if method not in [SafeRequestMethod.POST, SafeRequestMethod.PUT] else None,
                    cookies=self._cookies,
                    timeout=timeout,
                    allow_redirects=True,
                    default_headers=True,
                    verify=True,
                    http_version=self._version,
                    impersonate=self._impersonate,
                )

                return SafeRequestResponseData(
                    data=response.text,
                    status_code=response.status_code,
                    cookies=response.cookies,
                )
            except Exception as e:
                _LOGGER.error(f"Request failed for {url}: {e}")
                return SafeRequestResponseData()

async def fetch_buywisely_html(item_url: str):
    """Fetches the HTML content of a BuyWisely product page."""
    request_obj = SafeRequest()
    request_obj.user_agent(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3')
    
    response = await request_obj.request(
        method=SafeRequestMethod.GET,
        url=item_url,
    )
    
    if response.has:
        print(response.text)
    else:
        print(f"Failed to fetch HTML for {item_url}. Response was empty or error occurred.")

if __name__ == "__main__":
    # You can change this URL to a specific product page on BuyWisely
    sample_url = "https://www.buywisely.com.au/product/apple-iphone-15-pro-max-256gb-natural-titanium"
    asyncio.run(fetch_buywisely_html(sample_url))