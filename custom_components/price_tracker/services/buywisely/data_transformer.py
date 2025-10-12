"""Data transformation for BuyWisely product data."""

import logging
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import requests
from custom_components.price_tracker.services.buywisely.html_extractor import extract_from_beautifulsoup

from custom_components.price_tracker.datas.item import ItemData, ItemStatus
from custom_components.price_tracker.datas.price import ItemPriceData
from custom_components.price_tracker.datas.category import ItemCategoryData
from custom_components.price_tracker.utilities.parser import parse_float
from custom_components.price_tracker.datas.offer import ItemOfferData

from custom_components.price_tracker.services.buywisely.html_extractor import extract_from_beautifulsoup


_LOGGER = logging.getLogger(__name__)

def _validate_offer_price_against_seller_page(offer: dict, product_model: str) -> bool:
    """
    Validates the BuyWisely offer price against the price listed on the seller's product page.
    """
    seller_product_url = offer.get("seller_product_url")
    buywisely_price = offer.get("base_price")

    if not seller_product_url or buywisely_price is None:
        _LOGGER.warning(f"[DIAG][data_transformer] Skipping validation due to missing URL or BuyWisely price for offer: {offer}")
        return False

    try:
        response = requests.get(seller_product_url, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors
        seller_html = response.text

        # Use extract_from_beautifulsoup to get product data from the seller's page
        seller_product_data = extract_from_beautifulsoup(seller_html, excluded_domains=[])

        if seller_product_data and seller_product_data.get("offers"):
            # Assuming the seller_product_data will also have offers, we take the first one
            seller_listed_price = seller_product_data["offers"][0].get("base_price")
            if seller_listed_price is not None:
                # Compare prices with a small tolerance for floating point inaccuracies
                if abs(buywisely_price - seller_listed_price) < 0.01:
                    _LOGGER.debug(f"[DIAG][data_transformer] Price validated successfully for {seller_product_url}. BuyWisely: {buywisely_price}, Seller: {seller_listed_price}")
                    return True
                else:
                    _LOGGER.warning(f"[DIAG][data_transformer] Price mismatch for {seller_product_url}. BuyWisely: {buywisely_price}, Seller: {seller_listed_price}")
                    return False
            else:
                _LOGGER.warning(f"[DIAG][data_transformer] Could not extract listed price from seller page for {seller_product_url}.")
                return False
        else:
            _LOGGER.warning(f"[DIAG][data_transformer] No product offers found on seller page for {seller_product_url}.")
            return False

    except requests.exceptions.RequestException as e:
        _LOGGER.error(f"[DIAG][data_transformer] Error fetching seller page {seller_product_url}: {e}")
        return False
    except Exception as e:
        _LOGGER.error(f"[DIAG][data_transformer] Unexpected error during price validation for {seller_product_url}: {e}")
        return False


def transform_raw_product_data(
    raw_data: dict, product_model: str, item_url: str, excluded_domains: list[str]
) -> ItemData:
    """
    Transforms raw product data into an ItemData object, including seller page price validation.
    """
    offers = raw_data.get("offers", [])
    _LOGGER.debug(f"[DIAG][data_transformer] Raw offers: {offers}")
    _LOGGER.debug(f"[DIAG][data_transformer] Raw product model: {raw_data.get("model") or raw_data.get("name") or raw_data.get("title")}")
    lowest_price_value = None
    lowest_currency_value = ""
    seller_product_url = None
    status_value = ItemStatus.INACTIVE  # Initialize status_value to a default
    product_link = ""

    def model_in_url(url: str, model: str) -> bool:
        """Check if significant words from the product model are present in the seller product URL."""
        if not url or not model:
            return False
        url_lc = url.lower()
        model_words = re.findall(r'\b\w+\b', model.lower())
        # Filter out common, unhelpful words and ensure words are at least 3 characters long
        significant_words = [word for word in model_words if len(word) > 2 and word not in ["the", "and", "for", "with", "from", "new", "moto"]]

        # Require at least one significant word to be present in the URL
        return any(word in url_lc for word in significant_words)

    if offers:


        # Extract product model from raw_data (prefer 'model', fallback to 'name' or 'title')
        product_model = raw_data.get("model") or raw_data.get("name") or raw_data.get("title") or ""
        # Sort offers by base_price ascending
        def get_base_price(offer):
            base_price = offer.get("base_price", float("inf"))
            value = parse_float(base_price)
            if base_price is None or (
                isinstance(base_price, str) and not base_price.strip()
            ):
                return float("inf")
            return value

                # Iterate through sorted offers and validate them against the seller's page
                lowest_price_value = None
                lowest_currency_value = None
                product_link = None
                status_value = ItemStatus.PRICE_MISMATCH # Default to mismatch until a valid offer is found
        
                for offer in sorted_offers:
                    seller_product_url = offer.get("seller_product_url")
                    offer_price = offer.get("base_price")
                    offer_currency = offer.get("currency")
        
                    _LOGGER.info(f"[DIAG][offer] Checking offer: seller_product_url='{seller_product_url}', product_model='{product_model}', offer_price='{offer_price}', currency='{offer_currency}'")
        
                    if not seller_product_url:
                        _LOGGER.error(f"No seller_product_url found in offer: {offer}")
                        continue
        
                    # Seller Product URL Validation: must contain product model
                    url_valid = model_in_url(seller_product_url, product_model)
                    _LOGGER.info(f"[DIAG][offer] model_in_url result: {url_valid} for URL '{seller_product_url}' and model '{product_model}'")
        
                    if not url_valid:
                        _LOGGER.error(f"Seller product URL validation failed: URL '{seller_product_url}' does not contain expected model '{product_model}'. Skipping offer.")
                        continue
        
                    # Validate BuyWisely's price against the seller's page
                    if _validate_offer_price_against_seller_page(offer, product_model):
                        lowest_price_value = offer_price
                        lowest_currency_value = offer_currency
                        product_link = seller_product_url
                        status_value = ItemStatus.ACTIVE
                        _LOGGER.info(f"[DIAG][data_transformer] Validated offer selected: {seller_product_url} with price {offer_price} {offer_currency}")
                        break # Exit loop once a valid and validated offer is found
                    else:
                        _LOGGER.warning(f"[DIAG][data_transformer] Offer price validation failed for {seller_product_url}. Skipping this offer.")
        
                if lowest_price_value is None: # If no valid and validated offer was found
                    # Fallback to existing HTML parsing logic if no valid offer is found
                    # No valid seller_product_url in any offer: use item_url as URL
                    # But still try to use offer prices if available
                    product_link = item_url
                    # Try to use the lowest base_price from offers even if no seller_product_url
                    if fallback_offer and fallback_offer.get("base_price"):
                        lowest_price_value = fallback_offer.get("base_price")
                        lowest_currency_value = fallback_offer.get("currency")
                        _LOGGER.info(
                            f"Fallback: using lowest base_price {lowest_price_value} from offers despite no seller_product_url"
                        )
                    else:
                        # No prices in offers either: fallback to extracting price and currency from HTML
                        html = raw_data.get("html", "")
                        price_from_html = None
                        currency_from_html = None
                        if html:
                            soup = BeautifulSoup(html, "html.parser")
                            price_candidates = []
                            # Regex to match price and currency (captures currency symbol and value)
                            price_currency_regex = re.compile(
                                r"(?P<currency>\$|AUD|€|£|USD)?\s*(?P<price>\d{1,3}(?:[,.]?\d{3})*(?:[,.]\d{2})?)"
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
                                for match in price_currency_regex.finditer(text_node):
                                    price_text = match.group("price")
                                    currency_text = match.group("currency")
                                    cleaned_price_text = re.sub(r"[^\d,.]", "", price_text)
                                    if not cleaned_price_text:
                                        continue
                                    try:
                                        price_value = parse_float(cleaned_price_text)
                                        if price_value > 0:
                                            price_candidates.append(
                                                {
                                                    "price": price_value,
                                                    "currency": currency_text,
                                                    "text": match.group(0),
                                                }
                                            )
                                    except Exception:
                                        continue
                            if price_candidates:
                                # Prefer candidate with a currency symbol, else fallback to first
                                best = next(
                                    (c for c in price_candidates if c["currency"]),
                                    price_candidates[0],
                                )
                                price_from_html = best["price"]
                                currency_symbol = (
                                    best["currency"] or raw_data.get("currency") or "$"
                                )
                                # Normalize currency symbols to ISO codes
                                currency_map = {"€": "EUR", "£": "GBP"}
                                currency_from_html = currency_map.get(
                                    currency_symbol, currency_symbol
                                )
                                if currency_symbol == "$":
                                    # If it's a '$' symbol, we'll keep it as '$' for now and let a later stage determine the actual currency based on context (e.g., domain)
                                    currency_from_html = "$"
                                lowest_price_value = price_from_html
                                lowest_currency_value = currency_from_html
                                _LOGGER.info(
                                    f"Fallback: extracted price from HTML: {price_from_html}, currency: {currency_from_html}"
                                )
                            else:
                                lowest_price_value = 0.0
                                lowest_currency_value = raw_data.get("currency")
                                _LOGGER.error(
                                    "Fallback: could not extract price from HTML. Setting price to 0.0."
                                )
                        else:
                            lowest_price_value = 0.0
                            lowest_currency_value = raw_data.get("currency")
                            _LOGGER.error(
                                "Fallback: no HTML available. Setting price to 0.0."
                            )
        


    price_value = (
        lowest_price_value if lowest_price_value is not None else raw_data.get("price")
    )
    price_value = parse_float(price_value) if price_value is not None else None
    # Always default currency to 'AUD' if missing or empty
    currency_value = lowest_currency_value or raw_data.get("currency")

    brand_value = raw_data.get("brand") or ""
    description_value = raw_data.get("description") or ""
    category_value = raw_data.get("category") or ""
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

    item_offers = []
    if offers:
        for offer in offers:
            item_offers.append(
                ItemOfferData(
                    seller=offer.get("seller"),
                    price=offer.get("base_price"),
                    currency=offer.get("currency"),
                    url=offer.get("seller_product_url"),
                )
            )

    if not currency_value or currency_value == "$":
        from urllib.parse import urlparse
        parsed_url = urlparse(item_url)
        domain = parsed_url.netloc

        if "amazon.com.au" in domain:
            currency_value = "AUD"
        elif "amazon.com" in domain:
            currency_value = "USD"
        else:
            _LOGGER.warning(f"[DIAG][data_transformer] Could not determine currency for domain {domain}. Defaulting to AUD.")
            currency_value = "AUD"

    return ItemData(
        id=product_id,
        name=name_value,
        url=product_link,
        price=ItemPriceData(price=price_value, currency=currency_value),
        status=status_value,
        brand=brand_value,
        description=description_value,
        category=ItemCategoryData(category_value),
        image=image_value,
        offers=item_offers,
    )


async def _fetch_and_parse_seller_price(*args, **kwargs):
    raise AttributeError("This is a placeholder and should be mocked in tests.")
