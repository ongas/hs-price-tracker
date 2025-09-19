import logging
from custom_components.price_tracker.services.buywisely.json_parser import extract_and_parse_all_hydration_data

_LOGGER = logging.getLogger(__name__)

def parse_nextjs_hydration_data(html: str) -> list:
    """
    Extracts Next.js hydration data from HTML using BeautifulSoup and demjson3.
    Supports both <script id="__NEXT_DATA__"> and self.__next_f.push() formats.
    """
    return extract_and_parse_all_hydration_data(html)
