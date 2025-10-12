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


def _normalize_price_for_matching(price: float) -> list[str]:
    """
    Generate normalized variants of a price for string matching.

    E.g., 399.99 → ["399.99", "399", "39999", "$399.99", "AUD 399.99", "399,99", etc.]
    """
    variants = []
    # Base formats
    variants.append(str(price))  # "399.99"
    variants.append(str(int(price)))  # "399"
    variants.append(str(price).replace(".", ""))  # "39999"
    variants.append(str(price).replace(".", ","))  # "399,99"

    # With currency symbols/codes
    for prefix in ["$", "AUD", "AUD$", "USD", "€", "EUR", "£", "GBP"]:
        variants.append(f"{prefix}{price}")  # "$399.99"
        variants.append(f"{prefix} {price}")  # "$ 399.99"
        variants.append(f"{prefix}{int(price)}")  # "$399"

    # With formatting
    if price >= 1000:
        formatted = f"{price:,.2f}"  # "1,399.99"
        variants.append(formatted)
        variants.append(f"${formatted}")
        variants.append(f"AUD {formatted}")

    return variants


def _extract_all_prices_from_html(html: str) -> list[dict]:
    """
    Extract all price-like values from HTML (JSON + text).

    Returns a list of dicts with: price (float), text (original string), context (surrounding info).
    """
    import json

    soup = BeautifulSoup(html, "html.parser")
    all_prices = []

    # 1. Extract from JSON in <script> tags
    for script_tag in soup.find_all("script"):
        script_content = script_tag.string or script_tag.text or ""
        script_content = script_content.strip()
        if not script_content:
            continue
        try:
            data = json.loads(script_content)
        except Exception:
            continue

        def _find_prices_in_json(data, path=""):
            """Recursively find all prices in JSON."""
            prices = []
            if isinstance(data, dict):
                for key, value in data.items():
                    current_path = f"{path}.{key}" if path else key
                    if isinstance(key, str) and key.lower() in [
                        "price",
                        "base_price",
                        "amount",
                        "priceamount",
                    ]:
                        if isinstance(value, (int, float)) and value > 0:
                            prices.append(
                                {
                                    "price": float(value),
                                    "text": str(value),
                                    "context": f"JSON path: {current_path}",
                                    "source": "json",
                                }
                            )
                        elif isinstance(value, str):
                            try:
                                parsed = parse_float(value)
                                if parsed > 0:
                                    prices.append(
                                        {
                                            "price": parsed,
                                            "text": value,
                                            "context": f"JSON path: {current_path}",
                                            "source": "json",
                                        }
                                    )
                            except (ValueError, TypeError):
                                pass
                    prices.extend(_find_prices_in_json(value, current_path))
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    prices.extend(_find_prices_in_json(item, f"{path}[{i}]"))
            return prices

        all_prices.extend(_find_prices_in_json(data))

    # 2. Extract from HTML text
    price_regex = re.compile(
        r"(?:\$|AUD|€|£|USD)?\s*\d{1,3}(?:[,.]\d{3})*(?:[,.]\d{2})?"
    )

    for text_node in soup.find_all(string=True):
        if text_node.parent.name in [
            "script",
            "style",
            "head",
            "title",
            "meta",
            "[document]",
        ]:
            continue

        for match in price_regex.finditer(text_node):
            price_text = match.group(0)
            cleaned = re.sub(r"[^\d,.]", "", price_text)
            if not cleaned:
                continue

            try:
                price_value = parse_float(cleaned)
                if price_value > 0:
                    parent = text_node.parent
                    parent_text = parent.get_text(strip=True).lower() if parent else ""

                    # Extract class names from parent hierarchy
                    classes = []
                    for p in [parent] + list(parent.parents)[:3] if parent else []:
                        if p and hasattr(p, "get") and p.get("class"):
                            classes.extend(p.get("class", []))

                    all_prices.append(
                        {
                            "price": price_value,
                            "text": price_text,
                            "context": f"Text: '{parent_text[:50]}...', Classes: {','.join(classes[:3])}",
                            "source": "html",
                            "parent_text": parent_text,
                            "classes": classes,
                        }
                    )
            except (ValueError, TypeError):
                continue

    return all_prices


def _score_price_match(price_info: dict, expected_price: float) -> tuple[str, int, str]:
    """
    Score a price match by context to determine confidence.

    Returns: (confidence_level, occurrences_count, reasoning)
    - confidence_level: "HIGH", "MEDIUM", "LOW", or "REJECT"
    """
    parent_text = price_info.get("parent_text", "").lower()
    classes = [c.lower() for c in price_info.get("classes", [])]
    source = price_info.get("source", "")

    # Check for non-product contexts (reject)
    non_product_keywords = [
        "shipping",
        "delivery",
        "from $",
        "save $",
        "save up to",
        "was $",
        "discount",
        "related",
        "also bought",
        "similar",
    ]
    for keyword in non_product_keywords:
        if keyword in parent_text:
            return ("REJECT", 1, f"Found in non-product context: '{keyword}'")

    # Check for product price context (high/medium confidence)
    product_price_keywords = [
        "product-price",
        "price",
        "sale-price",
        "current-price",
        "our-price",
        "buy-price",
    ]
    has_product_context = any(
        keyword in " ".join(classes) for keyword in product_price_keywords
    )

    # JSON source gets medium confidence by default (structured data)
    if source == "json":
        return ("MEDIUM", 1, "Found in structured JSON data")

    # High confidence: clear product price context
    if has_product_context:
        return (
            "HIGH",
            1,
            f"Found in product price context. Classes: {','.join(classes[:3])}",
        )

    # Low confidence: found but no clear context
    return ("LOW", 1, "Found price but no clear product price context")


async def _fetch_and_parse_seller_price(
    url: str, expected_price: float
) -> Optional[float]:
    """
    Hybrid price validation: Extract all prices from seller page, match against expected price,
    and score by context to verify it's the product price.

    Returns: extracted price (float) if validation succeeds, None otherwise.
    """
    request = SafeRequest()
    try:
        response = await request.request(
            method=SafeRequestMethod.GET, url=url, post_try_callables=[]
        )
        if not response.has:
            _LOGGER.error(
                "Price validation failed: Failed to fetch seller page: %s", url
            )
            return None

        html_text = response.text if response.text is not None else ""

        # Step 1: Extract all prices from page
        all_prices = _extract_all_prices_from_html(html_text)

        if not all_prices:
            _LOGGER.warning(
                "Price validation failed: Could not extract any prices from seller page %s",
                url,
            )
            # Accept BuyWisely data but log for investigation
            return expected_price

        # Step 2: Normalize expected price into variants
        price_variants = _normalize_price_for_matching(expected_price)
        _LOGGER.info(
            f"[DIAG] Expected price: {expected_price}, Variants: {price_variants[:5]}..."
        )

        # Step 3: Match extracted prices against variants
        matched_prices = []
        for extracted in all_prices:
            extracted_str = str(extracted["price"])
            # Check if extracted price matches any variant (with tolerance)
            if any(
                variant in extracted["text"]
                or abs(extracted["price"] - expected_price) <= 0.01
                for variant in price_variants
            ):
                matched_prices.append(extracted)

        _LOGGER.info(
            f"[DIAG] Extracted {len(all_prices)} prices, {len(matched_prices)} matched expected price"
        )

        if not matched_prices:
            _LOGGER.error(
                f"Price validation failed: Expected price {expected_price} not found on seller page {url}. Extracted prices: {[p['price'] for p in all_prices[:10]]}"
            )
            return None

        # Step 4: Score matches by context
        scored_matches = []
        for match in matched_prices:
            confidence, count, reasoning = _score_price_match(match, expected_price)
            scored_matches.append(
                {**match, "confidence": confidence, "reasoning": reasoning}
            )

        # Step 5: Make decision based on confidence
        # Sort by confidence priority: HIGH > MEDIUM > LOW, reject REJECT
        confidence_order = {"HIGH": 3, "MEDIUM": 2, "LOW": 1, "REJECT": 0}
        valid_matches = [m for m in scored_matches if m["confidence"] != "REJECT"]

        if not valid_matches:
            _LOGGER.error(
                f"Price validation uncertain: Found {expected_price} on seller page but context suggests it's not the product price. Context: {scored_matches[0]['reasoning'] if scored_matches else 'N/A'}"
            )
            return None

        # Use highest confidence match
        valid_matches.sort(
            key=lambda x: confidence_order[x["confidence"]], reverse=True
        )
        best_match = valid_matches[0]

        if best_match["confidence"] == "HIGH":
            _LOGGER.info(
                f"Price validation succeeded: Found {expected_price} on seller page with HIGH confidence. Context: {best_match['reasoning']}"
            )
            return best_match["price"]
        elif best_match["confidence"] == "MEDIUM":
            _LOGGER.info(
                f"Price validation succeeded: Found {expected_price} on seller page with MEDIUM confidence. Context: {best_match['reasoning']}"
            )
            return best_match["price"]
        else:  # LOW
            _LOGGER.warning(
                f"Price validation low confidence: Found {expected_price} once on seller page with no product context. Accepting with warning. Context: {best_match['reasoning']}"
            )
            return best_match["price"]

    except Exception as e:
        _LOGGER.error("Error fetching/parsing seller page %s: %s", url, e)
        return None


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

    def model_in_url(url: str, model: str) -> bool:
        """Check if the product model or identifier is present in the seller product URL."""
        if not url or not model:
            return False
        url_lc = url.lower()
        model_lc = model.lower().replace(" ", "-").replace("_", "-")
        # Accept if model appears in path or query string
        return model_lc in url_lc

    if offers:
        from custom_components.price_tracker.utilities.parser import parse_float

        product_model = (
            raw_data.get("model") or raw_data.get("name") or raw_data.get("title") or ""
        )

        def get_base_price(offer):
            base_price = offer.get("base_price", float("inf"))
            value = parse_float(base_price)
            if base_price is None or (
                isinstance(base_price, str) and not base_price.strip()
            ):
                return float("inf")
            return value

        sorted_offers = sorted(offers, key=get_base_price)
        matched = False
        for offer in sorted_offers:
            seller_product_url = offer.get("seller_product_url")
            offer_price = offer.get("base_price")
            offer_currency = offer.get("currency", "AUD")
            _LOGGER.info(
                f"[DIAG][offer] Checking offer: seller_product_url='{seller_product_url}', product_model='{product_model}', offer_price='{offer_price}', currency='{offer_currency}'"
            )
            if not seller_product_url:
                _LOGGER.error(f"No seller_product_url found in offer: {offer}")
                continue
            url_valid = model_in_url(seller_product_url, product_model)
            _LOGGER.info(
                f"[DIAG][offer] model_in_url result: {url_valid} for URL '{seller_product_url}' and model '{product_model}'"
            )
            if not url_valid:
                _LOGGER.error(
                    f"Seller product URL validation failed: URL '{seller_product_url}' does not contain expected model '{product_model}'. Skipping offer."
                )
                continue
            expected_price = parse_float(offer_price)
            seller_page_price = await _fetch_and_parse_seller_price(
                seller_product_url, expected_price
            )
            _LOGGER.info(
                f"[DIAG][offer] Price comparison: BuyWisely price={expected_price}, Seller page price={seller_page_price}, abs diff={abs(seller_page_price - expected_price) if seller_page_price is not None else 'N/A'}"
            )
            if (
                seller_page_price is not None
                and abs(seller_page_price - expected_price) <= 0.01
            ):
                _LOGGER.info(
                    f"[DIAG][offer] MATCHED: seller_product_url='{seller_product_url}', product_model='{product_model}', price={expected_price}"
                )
                lowest_price_value = offer_price
                lowest_currency_value = offer_currency
                status_value = ItemStatus.ACTIVE
                product_link = seller_product_url
                matched = True
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
        if not matched:
            status_value = ItemStatus.PRICE_MISMATCH
            lowest_price_value = None
            lowest_currency_value = ""
            product_link = ""
            _LOGGER.error(
                f"No valid offer found for product_id={product_id}. Setting price to None and status to PRICE_MISMATCH."
            )

    from custom_components.price_tracker.utilities.parser import parse_float

    price_value = (
        lowest_price_value if lowest_price_value is not None else raw_data.get("price")
    )
    price_value = parse_float(price_value) if price_value is not None else None
    # Always default currency to 'AUD' if missing or empty
    currency_value = lowest_currency_value or raw_data.get("currency") or "AUD"
    brand_value = raw_data.get("brand") or ""
    # Prefer user-friendly product title from hydration data, fallback to user-friendly HTML element, then <title> as last resort
    name_value = None
    name_fields = ["title", "name"]
    for field in name_fields:
        name_raw = raw_data.get(field)
        if isinstance(name_raw, str) and name_raw.strip():
            name_value = name_raw.strip()
            _LOGGER.info(
                f"[DIAG][data_transformer] Extracted user-friendly product name from field '{field}': {name_value}"
            )
            break
    # Fallback: try to extract from user-friendly HTML element (h1, h2, class/id with 'title' or 'product-name')
    if not name_value and "html" in raw_data:
        soup = BeautifulSoup(raw_data["html"], "html.parser")
        # Try h1 or h2 with non-empty text
        for tag in ["h1", "h2"]:
            el = soup.find(tag)
            if el and el.text.strip():
                name_value = el.text.strip()
                _LOGGER.info(
                    f"[DIAG][data_transformer] Fallback: extracted product name from <{tag}>: {name_value}"
                )
                break
        # Try class or id containing 'title' or 'product-name'
        if not name_value:
            el = soup.find(attrs={"class": re.compile(r"(title|product-name)", re.I)})
            if el and el.text.strip():
                name_value = el.text.strip()
                _LOGGER.info(
                    f"[DIAG][data_transformer] Fallback: extracted product name from class: {name_value}"
                )
        if not name_value:
            el = soup.find(attrs={"id": re.compile(r"(title|product-name)", re.I)})
            if el and el.text.strip():
                name_value = el.text.strip()
                _LOGGER.info(
                    f"[DIAG][data_transformer] Fallback: extracted product name from id: {name_value}"
                )
        # As last resort, use <title>
        if not name_value:
            title_tag = soup.find("title")
            if title_tag and title_tag.text.strip():
                name_value = title_tag.text.strip()
                _LOGGER.info(
                    f"[DIAG][data_transformer] Last resort: extracted product name from <title>: {name_value}"
                )
    if not name_value:
        name_value = "UNKNOWN"
        _LOGGER.warning(
            f"Product name not found in user-friendly fields, HTML, or <title>, defaulting to 'UNKNOWN'. raw_data keys: {list(raw_data.keys())}"
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
