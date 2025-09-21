import logging
import re
from bs4 import BeautifulSoup

_LOGGER = logging.getLogger(__name__)

def extract_next_data_json_string(html: str) -> str | None:
    """
    Extracts the JSON string from <script id="__NEXT_DATA__"> tag.
    """
    soup = BeautifulSoup(html, 'html.parser')
    next_data_script = soup.find('script', {'id': '__NEXT_DATA__'})
    if next_data_script and next_data_script.string:
        return next_data_script.string
    return None

def extract_next_f_push_json_strings(html: str) -> list[str]:
    """
    Extracts JSON strings from self.__next_f.push() calls.
    """
    soup = BeautifulSoup(html, 'html.parser')
    json_strings = []
    for script in soup.find_all('script'):
        if script.string and 'self.__next_f.push' in script.string:
            matches = re.findall(r'self\.__next_f\.push\((.*?)\)', script.string, re.DOTALL)
            for match in matches:
                _LOGGER.debug(f"[DIAG][json_parser] Raw self.__next_f.push() match: {match}")
                json_strings.append(match)
    return json_strings
