import logging
from .hydration_parser import extract_and_parse_all_hydration_data

class NextJSHydrationDataExtractor:
    def __init__(self):
        self._logger = logging.getLogger(__name__)

    def parse(self, html: str):
        """
        Extracts and parses all Next.js hydration data from HTML using the robust parser.
        Returns the first product data found, or an empty dict if none found.
        """
        try:
            hydration_data_list = extract_and_parse_all_hydration_data(html)
            if hydration_data_list:
                self._logger.info(f"[NextJSHydrationDataExtractor] Found {len(hydration_data_list)} hydration data objects.")
                return hydration_data_list[0]
            else:
                self._logger.warning("[NextJSHydrationDataExtractor] No hydration data found.")
                return {}
        except Exception as e:
            self._logger.error(f"[NextJSHydrationDataExtractor] Exception during hydration parsing: {e}")
            return {}
