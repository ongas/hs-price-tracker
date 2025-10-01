import logging
import re
import demjson3
import os
from typing import Optional
from bs4 import BeautifulSoup
from .hydration_parser import extract_and_parse_all_hydration_data


_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.WARNING)


def _find_product_data_recursive(data, path=""):
    # _LOGGER.debug("[DIAG][_find_product_data_recursive] path: %s, type: %s", path, type(data))
    if isinstance(data, dict):
        # Accept either 'title' or 'name' as the product name field, with 'offers' present
        if (
            ("title" in data or "name" in data)
            and "offers" in data
            and isinstance(data["offers"], list)
        ):
            # _LOGGER.debug("[DIAG][_find_product_data_recursive] Found product data at path: %s", path)
            return data
        # Legacy: dict with 'product' key
        if "product" in data and isinstance(data["product"], dict):
            # _LOGGER.debug("[DIAG][_find_product_data_recursive] Found legacy product data at path: %s", path)
            return data["product"]
        for key, value in data.items():
            result = _find_product_data_recursive(value, f"{path}.{key}")
            if result:
                return result
    elif isinstance(data, list):
        if len(data) < 5:
            pass
        else:
            pass
        for i, item in enumerate(data):
            result = _find_product_data_recursive(item, f"{path}[{i}]")
            if result:
                return result
    return None


def extract_from_beautifulsoup(html: str) -> dict:
    """Extracts product data using BeautifulSoup fallback."""
    soup = BeautifulSoup(html, "html.parser")
    price_val = None
    currency_val = "AUD"
    price_text = None
    title_val = None
    seller_url = None

    # Try to extract product name/title from <title>, <h1>, meta tags, or slug field in scripts
    title_elem = soup.find("title")
    if title_elem and title_elem.get_text(strip=True):
        title_val = title_elem.get_text(strip=True)
    # _LOGGER.info(f"[DIAG][html_extractor] Extracted product title from <title>: {title_val}")
    else:
        h1_elem = soup.find("h1")
        if h1_elem and h1_elem.get_text(strip=True):
            title_val = h1_elem.get_text(strip=True)
            # _LOGGER.info(f"[DIAG][html_extractor] Extracted product title from <h1>: {title_val}")
        else:
            meta_title = soup.find("meta", attrs={"name": "og:title"}) or soup.find(
                "meta", attrs={"property": "og:title"}
            )
            if meta_title and meta_title.get("content"):
                title_val = meta_title.get("content").strip()
                # _LOGGER.info(f"[DIAG][html_extractor] Extracted product title from og:title meta: {title_val}")
    # If still not found, try to extract from slug in scripts
    if not title_val:
        for script in soup.find_all("script"):
            if script.string and "slug" in script.string:
                match = re.search(r'"slug"\s*:\s*"([^"]+)"', script.string)
                if match:
                    title_val = match.group(1)
                    # _LOGGER.info(f"[DIAG][html_extractor] Extracted product title from slug in script: {title_val}")
                    break

    # Try to extract seller URL from anchor tags with likely hrefs
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("http") and "product" in href:
            seller_url = href
            # _LOGGER.info(f"[DIAG][html_extractor] Extracted seller URL from anchor: {seller_url}")
            break
    # If not found, try to extract from any script or JSON block containing seller_product_url
    if not seller_url:
        for script in soup.find_all("script"):
            if script.string and "seller_product_url" in script.string:
                match = re.search(
                    r'"seller_product_url"\s*:\s*"([^"]+)"', script.string
                )
                if match:
                    seller_url = match.group(1)
                    # _LOGGER.info(f"[DIAG][html_extractor] Extracted seller URL from script: {seller_url}")
                    break

    # Try to extract price from <h3> and <h2> tags with price-like content
    price_candidates = []
    for tag in soup.find_all(["h3", "h2"]):
        text = tag.get_text(strip=True)
        if re.search(r"\$\s*\d", text):
            # Extract all price values from the string
            found_prices = re.findall(r"\$\s*([\d,.]+)", text)
            for p in found_prices:
                try:
                    price_candidates.append(float(p.replace(",", "")))
                except Exception:
                    pass
            if found_prices:
                pass

    # If multiple prices, pick the lowest
    if price_candidates:
        price_val = min(price_candidates)
        price_text = f"${price_val:.2f}"
        currency_val = "AUD"
        pass
    else:
        # Fallback to previous logic
        price_elem = soup.find(class_="price")
        if price_elem:
            price_text = price_elem.get_text(strip=True)
        elif not price_text:
            for t in soup.find_all(string=True):
                if re.search(r"\$|AUD|EUR|₩|¥|원|円", t):
                    price_text = t.strip()
                    break

        if price_text:
            currency_match = re.search(
                r"(AUD|EUR|₩|¥|원|円|USD|NZD|GBP|\$)", price_text
            )
            if currency_match:
                if currency_match.group(1) == "$":
                    currency_val = "AUD"
                else:
                    currency_val = currency_match.group(1)
            else:
                currency_val = "AUD"

            price_match = re.search(r"([\d,.]+)", price_text.replace(",", ""))
            if price_match:
                try:
                    price_val = float(price_match.group(1))
                except Exception:
                    price_val = None
            else:
                price_val = None

    raw_data = {"html": html}
    if price_val is not None:
        raw_data["price"] = price_val
        raw_data["currency"] = currency_val
        raw_data["availability"] = "In Stock"
        raw_data["brand"] = ""
        raw_data["title"] = title_val if title_val else ""
        raw_data["name"] = title_val if title_val else ""
        raw_data["url"] = seller_url if seller_url else ""
        # Insert extracted offer if possible
        offer = {}
        if seller_url:
            offer["seller_product_url"] = seller_url
        if price_val is not None:
            offer["base_price"] = price_val
        if currency_val:
            offer["currency"] = currency_val
        raw_data["offers"] = [offer] if offer else []
    else:
        raw_data["availability"] = "Out of Stock"
        raw_data["title"] = title_val if title_val else ""
        raw_data["name"] = title_val if title_val else ""
        raw_data["url"] = seller_url if seller_url else ""
        raw_data["offers"] = []
    # Always include the original HTML for fallback extraction
    return raw_data


async def extract_product_data_from_html(html: str) -> dict:
    """Extracts product data from BuyWisely HTML content."""
    parsed_data_list = []
    try:
        parsed_data_list = extract_and_parse_all_hydration_data(html)
        try:
            pass
            # _LOGGER.info("[DIAG][html_extractor] Full parsed_data (hydration): %s", _json.dumps(parsed_data_list, default=str)[:10000])
        except Exception as e:
            _LOGGER.error(
                "[DIAG][html_extractor] Exception logging full parsed_data: %s", e
            )
    except Exception as e:
        _LOGGER.error(
            "BuyWisely HtmlExtractor: Error parsing with hydration_parser: %s", e
        )
        parsed_data_list = []

    if not parsed_data_list:
        _LOGGER.warning(
            "[DIAG] HydrationDataExtractor returned empty, attempting manual __NEXT_DATA__ extraction."
        )
        match = re.search(
            r'<script\s+[^>]*id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>',
            html,
            re.DOTALL,
        )
        if match:
            try:
                next_data_json = match.group(1).strip()
                parsed_data_manual = demjson3.decode(next_data_json)
                _LOGGER.info(
                    f"[DIAG] Manually extracted __NEXT_DATA__ JSON: {type(parsed_data_manual)}"
                )
                if isinstance(parsed_data_manual, list):
                    parsed_data_list.extend(parsed_data_manual)
                else:
                    parsed_data_list.append(parsed_data_manual)
            except Exception as e:
                _LOGGER.error(f"[DIAG] Failed to parse __NEXT_DATA__ JSON: {e}")
                parsed_data_list = []

    product_data = None
    for item in parsed_data_list:
        product_data = _find_product_data_recursive(item)
        if product_data:
            break
    # If recursive search failed but top-level dict has 'offers', try to extract product fields from offers
    if not product_data:
        for item in parsed_data_list:
            if isinstance(item, dict) and "offers" in item:
                product_data = item
                # If no title/name, try to extract from the first offer
                offers = product_data.get("offers", []) if product_data else []
                if product_data and not any(
                    k in product_data for k in ("title", "name")
                ):
                    if (
                        offers
                        and isinstance(offers, list)
                        and isinstance(offers[0], dict)
                    ):
                        for field in ("title", "name", "product"):
                            if field in offers[0] and isinstance(offers[0][field], str):
                                product_data[field] = offers[0][field]
                                break
                break
    # Always include the original HTML for fallback extraction
    # Patch: If product_data is missing 'title' and 'name', but has a nested 'product' dict, use that dict
    if product_data and isinstance(product_data, dict):
        if (
            not any(k in product_data for k in ("title", "name"))
            and "product" in product_data
            and isinstance(product_data["product"], dict)
        ):
            product_data = product_data["product"]
        # Prefer 'title' over 'slug' for name extraction
        title = product_data.get("title") or product_data.get("name") or ""
        brand = title.split(" ")[0] if title else ""
        # Only process current offers (those visible above 'See n more history offers')
        offers_list = product_data.get("offers", [])
        # Filter out history/hidden offers if present
        filtered_offers = []
        for offer in offers_list:
            # Heuristic: skip offers with 'history' or 'hidden' flag, or if marked as not visible
            if isinstance(offer, dict):
                if (
                    offer.get("history")
                    or offer.get("hidden")
                    or offer.get("is_history")
                    or offer.get("is_hidden")
                ):
                    _LOGGER.info(
                        f"[DIAG][html_extractor] Skipping history/hidden offer: {offer}"
                    )
                    continue
                filtered_offers.append(offer)
        product_data["offers"] = (
            filtered_offers if isinstance(filtered_offers, list) else []
        )
        offers, main_url, lowest_total, lowest_offer = _process_product_offers(
            product_data, return_lowest_details=True
        )
        selected_delivery = None
        if lowest_offer and isinstance(lowest_offer, dict):
            for key in ("delivery", "shipping"):
                val = lowest_offer.get(key)
                try:
                    selected_delivery = float(val) if val is not None else None
                except (ValueError, TypeError):
                    selected_delivery = None
                if selected_delivery is not None:
                    break
        # Use only the product 'title' field from hydration data for display and entity attributes
        name_value = product_data.get("title") or product_data.get("name") or ""
        price_val = lowest_total if lowest_total is not None else None
        currency_val = (
            lowest_offer.get("currency")
            if lowest_offer
            else product_data.get("currency", "AUD")
        )
        raw_data = {
            "title": name_value,
            "price": price_val,
            "image": product_data.get("image") if product_data else None,
            "currency": currency_val,
            "availability": "In Stock" if offers else "Out of Stock",
            "brand": brand if "brand" in locals() else "",
            "url": main_url,
            "offers": offers,
            "delivery_price": selected_delivery,
            "html": html,  # Always include the original HTML
        }
        return raw_data
    else:
        raw_data = extract_from_beautifulsoup(html)
        raw_data["html"] = html  # Always include the original HTML
        return raw_data


def _debug_local_html_parsing():
    html_path = os.path.join(
        os.path.dirname(__file__), "../../temp_manually_saved_html_pretty_print.html"
    )
    html_path = os.path.abspath(html_path)
    # _LOGGER.info("[DIAG][_debug_local_html_parsing] Loading HTML from: %s", html_path)
    if not os.path.exists(html_path):
        _LOGGER.error(
            "[DIAG][_debug_local_html_parsing] File does not exist: %s", html_path
        )
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            _html_content = f.read()
    # _LOGGER.info("[DIAG][_debug_local_html_parsing] Read %d bytes from HTML file.", len(_html_content))
    except Exception as e:
        _LOGGER.error(
            "[DIAG][_debug_local_html_parsing] Failed to read HTML file: %s", e
        )
        return
    # Extraction logic for local debug (sync context)
    # If you need to run async extraction, use asyncio.run()
    # For local debug, just call and ignore result
    # If extract_product_data_from_html is async, use: asyncio.run(extract_product_data_from_html(_html_content))
    pass


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s:%(message)s")
    _debug_local_html_parsing()


def _is_valid_seller_url(url: str, product_image_url: Optional[str]) -> bool:
    """Checks if a given URL is a valid seller product URL."""
    if not url or not isinstance(url, str):
        # _LOGGER.debug("[DIAG][is_valid_seller_url] Invalid: URL is None or not a string.")
        return False
    url = url.strip()
    if re.search(r"\.(jpg|jpeg|png|gif|webp|svg|bmp|tiff)(\?|$)", url, re.IGNORECASE):
        # _LOGGER.debug("[DIAG][is_valid_seller_url] Invalid: URL is an image URL.")
        return False
    if product_image_url and url == product_image_url:
        # _LOGGER.debug("[DIAG][is_valid_seller_url] Invalid: URL matches product image URL.")
        return False
    if re.search(r"buywisely\.com\.au", url, re.IGNORECASE):
        # _LOGGER.debug("[DIAG][is_valid_seller_url] Invalid: URL contains buywisely.com.au.")
        return False
    if not url.startswith("http"):
        # _LOGGER.debug("[DIAG][is_valid_seller_url] Invalid: URL does not start with http.")
        return False
    # _LOGGER.debug("[DIAG][is_valid_seller_url] Valid: URL passed all checks.")
    return True


def _process_product_offers(
    product_data: dict, return_lowest_details: bool = False
) -> tuple:
    """Processes product offers to find the main URL and filter offers. Optionally returns lowest price and offer."""
    offers = product_data.get("offers", [])
    if not isinstance(offers, list):
        offers = []

    # Filter to only current offers (exclude history offers)
    # Current offers are those with the maximum created_at timestamp
    if offers:
        max_created_at = max(
            offer.get("created_at", "")
            for offer in offers
            if isinstance(offer, dict)
        )
        current_offers = [
            offer
            for offer in offers
            if isinstance(offer, dict) and offer.get("created_at") == max_created_at
        ]
        # Limit to first 10 offers (initially visible offers)
        offers = current_offers[:10]
        _LOGGER.info(
            "[DIAG][html_extractor] Filtered to %d initially visible current offers (max_created_at: %s) from %d total offers",
            len(offers),
            max_created_at,
            len(product_data.get("offers", [])),
        )

    all_seller_urls = [
        offer.get("seller_product_url")
        for offer in offers
        if isinstance(offer, dict) and "seller_product_url" in offer
    ]
    _LOGGER.info(
        "[DIAG][html_extractor] All candidate seller_product_url values: %r",
        all_seller_urls,
    )

    lowest_offer = None
    lowest_total = None
    for offer in offers:
        if not isinstance(offer, dict):
            continue
        # Use price, fallback to base_price
        price = offer.get("price")
        if price is None:
            price = offer.get("base_price")
        if (
            price is None
            or price == ""
            or (isinstance(price, str) and not price.strip())
        ):
            _LOGGER.warning(
                "[DIAG] Offer has missing or empty price/base_price: %r", offer
            )
            continue
        try:
            price_val = float(price)
        except (ValueError, TypeError) as e:
            _LOGGER.warning("[DIAG] Could not parse price %r: %s", price, e)
            continue
        # Add delivery if present and numeric
        delivery = offer.get("delivery")
        delivery_val = 0.0
        if delivery is not None:
            try:
                delivery_val = float(delivery)
            except (ValueError, TypeError):
                _LOGGER.warning(
                    "[DIAG] Could not parse delivery %r for offer: %r", delivery, offer
                )
                delivery_val = 0.0
        total = price_val + delivery_val
        _LOGGER.info(
            "[DIAG][html_extractor] Offer: %r, price: %r, delivery: %r, total: %r",
            offer,
            price_val,
            delivery_val,
            total,
        )
        if lowest_total is None or total < lowest_total:
            lowest_total = total
            lowest_offer = offer

    main_url = ""
    url_candidate = lowest_offer.get("seller_product_url") if lowest_offer else ""
    image_candidate = product_data.get("image") if product_data else ""
    if lowest_offer and _is_valid_seller_url(str(url_candidate or ""), image_candidate):
        main_url = str(url_candidate)
        _LOGGER.info(
            "[DIAG][html_extractor] Extracted seller_product_url from lowest-priced offer: %r",
            main_url,
        )
    else:
        _LOGGER.error(
            "[html_extractor] No valid seller URL found in offers. Extraction failure."
        )
    if return_lowest_details:
        return offers, main_url, lowest_total, lowest_offer
    return offers, main_url
