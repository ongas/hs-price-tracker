import logging
import demjson3

_LOGGER = logging.getLogger(__name__)

def parse_with_tolerantjson_fallback(json_str: str):
    """
    Try to parse with demjson3, fallback to quoting/wrapping as string if it fails.
    """
    try:
        return demjson3.decode(json_str)
    except Exception as e:
        _LOGGER.warning(f"demjson3 failed to parse: {e}. Wrapping as string.")
        return str(json_str)

def robust_identifier_conversion(identifier_str: str):
    """
    Robustly convert identifier content using tolerantjson, fallback to string if needed.
    """
    try:
        return demjson3.decode(identifier_str)
    except Exception as e:
        _LOGGER.warning(f"Failed to parse identifier with demjson3: {e}. Returning as string.")
        return identifier_str
