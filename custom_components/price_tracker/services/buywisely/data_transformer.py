"""Data transformation for BuyWisely product data."""

import logging
import re
from typing import Optional
from bs4 import BeautifulSoup

from custom_components.price_tracker.datas.item import ItemData, ItemStatus
from custom_components.price_tracker.datas.price import ItemPriceData
from custom_components.price_tracker.datas.category import ItemCategoryData
from custom_components.price_tracker.utilities.safe_request import (
    SafeRequest,
    SafeRequestMethod,
)
from custom_components.price_tracker.utilities.parser import parse_float

_LOGGER = logging.getLogger(__name__)


async def _fetch_and_parse_seller_price(url: str) -> Optional[float]:
    """
    Fetches the seller's product page and attempts to extract the price.
    Returns the extracted price as a float, or None if extraction fails.
    """
    request = SafeRequest()
    try:
        response = await request.request(
            method=SafeRequestMethod.GET, url=url, post_try_callables=[]
        )
        if not response.has:
            _LOGGER.error("Failed to fetch seller page for price validation: %s", url)
            return None

        html_text = response.text if response.text is not None else ""
        soup = BeautifulSoup(html_text, "html.parser")

        # --- Start of new JSON parsing logic ---
        import json

        def _find_price_in_json(data):
            """Recursively search for a price in a JSON object."""
            if isinstance(data, dict):
                for key, value in data.items():
                    # Check if the key is a price-related term
                    if isinstance(key, str) and key.lower() in [
                        "price",
                        "base_price",
                        "amount",
                        "priceamount",
                    ]:
                        if isinstance(value, (int, float)):
                            return float(value)
                        if isinstance(value, str):
                            try:
                                return parse_float(value)
                            except (ValueError, TypeError):
                                pass  # Continue searching
                    # Recurse into the value
                    found_price = _find_price_in_json(value)
                    if found_price is not None:
                        return found_price
            elif isinstance(data, list):
                for item in data:
                    found_price = _find_price_in_json(item)
                    if found_price is not None:
                        return found_price
            return None

        # 1. Prioritize searching for price in JSON within <script> tags
        for script_tag in soup.find_all("script"):
            script_content = script_tag.string or script_tag.text or ""
            script_content = script_content.strip()
            if not script_content:
                continue
            try:
                data = json.loads(script_content)
            except Exception:
                # Ignore scripts that aren't valid JSON
                data = None
            if data is not None:
                price = _find_price_in_json(data)
                if price is not None:
                    return price
        # ...existing code...
    except Exception as e:
        _LOGGER.error("Error fetching/parsing seller page %s: %s", url, e)
        return None

    # --- End of new JSON parsing logic ---

    # 2. Fallback to searching HTML text if JSON search fails
    candidates = []
    # Regex to find price-like numbers (e.g., 1,234.56, $123.45, 1.234,56)
    price_regex = re.compile(
        r"(?:\$|AUD|€|£|USD)?\s*\d{1,3}(?:[,.]\d{3})*(?:[,.]\d{2})?"
    )

    for text_node in soup.find_all(string=True):
        # Avoid script and style tags
        if text_node.parent.name in [
            "script",
            "style",
            "head",
            "title",
            "meta",
            "[document]",
        ]:
            continue
        # Find all price-like strings in the text node
        for match in price_regex.finditer(text_node):
            price_text = match.group(0)
            score = 0

            # Clean the price text for parsing
            cleaned_price_text = re.sub(r"[^\d,.]", "", price_text)
            if not cleaned_price_text:
                continue

            # Scoring based on context
            parent = text_node.parent
            parent_text = parent.get_text().lower() if parent else ""

            # 1. Check for keywords in surrounding text
            if any(
                keyword in parent_text
                for keyword in ["price", "sale", "now", "was", "total", "aud", "$"]
            ):
                score += 2

            # 2. Check for class names in parent tags
            for p in [parent] + list(parent.parents) if parent else []:
                if p and hasattr(p, "get") and p.get("class"):
                    class_names = " ".join(p.get("class", [])).lower()
                    if any(
                        keyword in class_names
                        for keyword in ["price", "amount", "cost", "sale"]
                    ):
                        score += 3

            # 3. Penalize if it's likely part of a larger number or irrelevant string
            if "off" in parent_text or "%" in parent_text:
                score -= 2

            try:
                # Use a robust parsing function
                price_value = parse_float(cleaned_price_text)
                if price_value > 0:
                    candidates.append(
                        {"price": price_value, "score": score, "text": price_text}
                    )
            except (ValueError, TypeError):
                continue

        if not candidates:
            _LOGGER.warning("No price candidates found on seller page: %s", url)
            return None

        # Select the best candidate based on score
        # To handle cases where multiple candidates have the same high score,
        # we can add a secondary sorting criterion, e.g., preferring larger values
        # as they are more likely to be the main product price.
        candidates.sort(key=lambda x: (x["score"], x["price"]), reverse=True)

        best_candidate = candidates[0]
        return best_candidate["price"]
    # Removed unreachable except blocks


async def transform_raw_product_data(
    raw_data: dict, product_id: str, item_url: str
) -> ItemData:
    """
    Transforms raw product data into an ItemData object, including seller page price validation.
    """
    offers = raw_data.get("offers", [])
    lowest_price_value = None
    lowest_currency_value = ""
    seller_product_url = None
    status_value = ItemStatus.INACTIVE  # Initialize status_value to a default
    product_link = ""

    if offers:
        from custom_components.price_tracker.utilities.parser import parse_float

        # Sort offers by base_price ascending
        def get_base_price(offer):
            base_price = offer.get("base_price", float("inf"))
            value = parse_float(base_price)
            if base_price is None or (
                isinstance(base_price, str) and not base_price.strip()
            ):
                return float("inf")
            return value

        sorted_offers = sorted(offers, key=get_base_price)
        # Loop through sorted offers, validate price on seller page
        for offer in sorted_offers:
            seller_product_url = offer.get("seller_product_url")
            offer_price = offer.get("base_price")
            offer_currency = offer.get("currency", "AUD")
            if not seller_product_url:
                _LOGGER.error(f"No seller_product_url found in offer: {offer}")
                continue
            seller_page_price = await _fetch_and_parse_seller_price(seller_product_url)
            _LOGGER.info(
                f"[DIAG][data_transformer] Validating offer: {offer}, seller_page_price: {seller_page_price}"
            )
            if (
                seller_page_price is not None
                and abs(seller_page_price - parse_float(offer_price)) <= 0.01
            ):
                # Found a matching offer
                lowest_price_value = offer_price
                lowest_currency_value = offer_currency
                status_value = ItemStatus.ACTIVE
                product_link = seller_product_url
                break
            elif seller_page_price is None:
                _LOGGER.error(
                    f"Could not extract price from seller page for product_id={product_id}. Skipping offer."
                )
                continue
            else:
                _LOGGER.error(
                    f"Price mismatch for product_id={product_id}. BuyWisely price: {offer_price}, Seller page price: {seller_page_price}. Skipping offer."
                )
                continue
        else:
            # No matching offer found
            status_value = ItemStatus.PRICE_MISMATCH
            lowest_price_value = None
            lowest_currency_value = ""
            product_link = (
                sorted_offers[0].get("seller_product_url") if sorted_offers else ""
            )

    from custom_components.price_tracker.utilities.parser import parse_float

    price_value = (
        lowest_price_value if lowest_price_value is not None else raw_data.get("price")
    )
    price_value = parse_float(price_value) if price_value is not None else None
    # Always default currency to 'AUD' if missing or empty
    currency_value = lowest_currency_value or raw_data.get("currency") or "AUD"
    brand_value = raw_data.get("brand") or ""
    # Always extract product name from BuyWisely product page HTML <title>, fallback to other fields
    name_value = None
    if "html" in raw_data:
        soup = BeautifulSoup(raw_data["html"], "html.parser")
        title_tag = soup.find("title")
        if title_tag and title_tag.text.strip():
            name_value = title_tag.text.strip()
            _LOGGER.info(
                f"[DIAG][data_transformer] Extracted product name from BuyWisely <title>: {name_value}"
            )
    if not name_value:
        name_fields = ["title", "name", "product"]
        for field in name_fields:
            name_raw = raw_data.get(field)
            if isinstance(name_raw, str) and name_raw.strip():
                name_value = name_raw.strip()
                _LOGGER.info(
                    f"[DIAG][data_transformer] Extracted product name from field '{field}': {name_value}"
                )
                break
    if not name_value:
        name_fields = ["title", "name", "product"]
        name_value = "UNKNOWN"
        _LOGGER.warning(
            f"Product name not found in <title> or any of {name_fields}, defaulting to 'UNKNOWN'. raw_data keys: {list(raw_data.keys())}"
        )
    image_value = raw_data.get("image") or ""
    # Set status to INACTIVE if price is None or 0.0, or if not in stock
    # This logic is now partially superseded by seller page validation, but still relevant for initial extraction
    if status_value == ItemStatus.ACTIVE and (
        raw_data.get("availability") != "In Stock" or price_value in (None, 0.0)
    ):
        status_value = ItemStatus.INACTIVE

    def is_valid_seller_url(url):
        if not url or not isinstance(url, str):
            return False
        url = url.strip()
        if any(
            url.lower().endswith(ext)
            for ext in [
                ".jpg",
                ".jpeg",
                ".png",
                ".gif",
                ".webp",
                ".svg",
                ".bmp",
                ".tiff",
            ]
        ):
            return False
        if "buywisely.com.au" in url.lower():
            return False
        if not url.startswith("http"):
            return False
        return True

    # Always use the seller_product_url for BuyWisely
    extracted_url = seller_product_url
    if is_valid_seller_url(extracted_url):
        product_link = extracted_url
    else:
        product_link = ""
        _LOGGER.error(
            f"No valid seller product URL found in offers for product_id={product_id}. Extraction failure."
        )

    price = (
        ItemPriceData(price=price_value, currency=currency_value)
        if price_value is not None and currency_value
        else ItemPriceData(price=0.0, currency="")
    )

    result = ItemData(
        id=product_id,
        name=name_value,
        brand=brand_value,
        url=product_link or "",
        status=status_value,
        price=price,
        image=image_value,
        category=ItemCategoryData(None),
    )
    return result
