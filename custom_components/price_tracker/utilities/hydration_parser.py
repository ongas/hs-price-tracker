
import json
import logging
import re
from bs4 import BeautifulSoup
import demjson3

_LOGGER = logging.getLogger(__name__)

def parse_nextjs_hydration_data(html: str) -> list:
    """
    Extracts Next.js hydration data from HTML using BeautifulSoup and demjson3.
    Supports both <script id="__NEXT_DATA__"> and self.__next_f.push() formats.
    """
    results = []
    soup = BeautifulSoup(html, 'html.parser')

    # 1. Find legacy __NEXT_DATA__ script
    next_data_script = soup.find('script', {'id': '__NEXT_DATA__'})
    if next_data_script:
        try:
            json_text = next_data_script.string
            data = demjson3.decode(json_text)
            results.append(data)
            _LOGGER.info("Successfully parsed __NEXT_DATA__ with demjson3.")
        except demjson3.JSONDecodeError as e:
            _LOGGER.warning(f"demjson3 failed to parse __NEXT_DATA__, trying standard json: {e}")
            try:
                data = json.loads(json_text)
                results.append(data)
                _LOGGER.info("Successfully parsed __NEXT_DATA__ with standard json.")
            except json.JSONDecodeError as json_err:
                _LOGGER.error(f"Failed to parse __NEXT_DATA__ with both demjson3 and json: {json_err}")

    # 2. Find new self.__next_f.push() scripts
    for script in soup.find_all('script'):
        if script.string and 'self.__next_f.push' in script.string:
            matches = re.findall(r'self\.__next_f\.push\((.*?)\)', script.string, re.DOTALL)
            for match in matches:
                try:
                    # The match is typically a list-like string, e.g., '[1, "33:{...}"]'
                    arr = demjson3.decode(match)
                    if len(arr) > 1 and isinstance(arr[1], str) and ':' in arr[1]:
                        chunk_id, json_str = arr[1].split(':', 1)
                        data = demjson3.decode(json_str)
                        results.append({
                            'chunk_id': str(arr[0]),
                            'extracted_data': [{
                                'type': 'colon_separated',
                                'identifier': chunk_id,
                                'data': data
                            }],
                        })
                        _LOGGER.info(f"Successfully parsed self.__next_f.push chunk {chunk_id} with demjson3.")
                except demjson3.JSONDecodeError as e:
                    _LOGGER.warning(f"demjson3 failed to parse self.__next_f.push chunk, trying standard json: {e}")
                    try:
                        arr = json.loads(match)
                        if len(arr) > 1 and isinstance(arr[1], str) and ':' in arr[1]:
                            chunk_id, json_str = arr[1].split(':', 1)
                            data = json.loads(json_str)
                            results.append({
                                'chunk_id': str(arr[0]),
                                'extracted_data': [{
                                    'type': 'colon_separated',
                                    'identifier': chunk_id,
                                    'data': data
                                }],
                            })
                            _LOGGER.info(f"Successfully parsed self.__next_f.push chunk {chunk_id} with standard json.")
                    except json.JSONDecodeError as json_err:
                        _LOGGER.error(f"Failed to parse self.__next_f.push chunk with both demjson3 and json: {json_err}")

    _LOGGER.info(f"Hydration parser found {len(results)} data object(s).")
    return results
