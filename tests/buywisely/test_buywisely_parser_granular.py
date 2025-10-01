import os
from custom_components.price_tracker.services.buywisely.hydration_parser import (
    extract_and_parse_all_hydration_data,
)

FIXTURE_PATH = "tests/buywisely/fixtures/real_buywisely_product.html"


def test_fixture_file_exists_and_nonempty():
    assert os.path.exists(FIXTURE_PATH), "Fixture file does not exist."
    with open(FIXTURE_PATH, "r") as f:
        data = f.read()
    assert data.strip(), "Fixture file is empty."


def wrap_in_html_script_tag(payload: str) -> str:
    return f'<html><head></head><body><script type="text/javascript">\n{payload}\n</script></body></html>'


def test_hydration_parser_raw_parse():
    with open(FIXTURE_PATH, "r") as f:
        html = f.read()
    parsed = extract_and_parse_all_hydration_data(html)
    assert parsed is not None, "Parser returned None."
    assert isinstance(parsed, list), f"Parser did not return a list: {type(parsed)}"
    assert len(parsed) > 0, "Parser returned empty list."


def test_hydration_parser_find_product():
    with open(FIXTURE_PATH, "r") as f:
        html = f.read()
    parsed = extract_and_parse_all_hydration_data(html)
    product = None
    for obj in parsed:
        if isinstance(obj, dict) and "offers" in obj:
            product = obj
            break
    assert product is not None, "No product dict with offers found."


def test_hydration_parser_find_offers():
    with open(FIXTURE_PATH, "r") as f:
        html = f.read()
    parsed = extract_and_parse_all_hydration_data(html)
    offers = None
    for obj in parsed:
        if isinstance(obj, dict) and "offers" in obj:
            offers = obj["offers"]
            break
    assert offers is not None, "No offers list found in product dict."
    assert isinstance(offers, list), f"Offers is not a list: {type(offers)}"
    assert len(offers) > 0, "Offers list is empty."


def test_hydration_parser_offer_fields():
    with open(FIXTURE_PATH, "r") as f:
        html = f.read()
    parsed = extract_and_parse_all_hydration_data(html)
    print("[DIAG] Parsed object:", parsed)
    offers = None
    # If parsed is a list, search for offers in each dict
    if isinstance(parsed, list):
        for obj in parsed:
            if isinstance(obj, dict) and "offers" in obj:
                offers = obj["offers"]
                break
    elif isinstance(parsed, dict) and "offers" in parsed:
        offers = parsed["offers"]
    print("[DIAG] Offers (all):", offers)
    if offers:
        for idx, offer in enumerate(offers):
            print(f"[DIAG] Offer {idx}: keys={list(offer.keys())}, offer={offer}")
    # Print all product dicts in parsed list that contain 'offers'
    if isinstance(parsed, list):
        for idx, obj in enumerate(parsed):
            if isinstance(obj, dict) and "offers" in obj:
                print(
                    f"[DIAG] Product dict {idx} with offers: keys={list(obj.keys())}, product={obj}"
                )
    assert offers is not None and len(offers) > 0, "No offers found."
    offer = offers[0]
    print("[DIAG] First offer:", offer)
    assert isinstance(offer, dict), f"First offer is not a dict: {type(offer)}"
    assert (
        "price" in offer or "base_price" in offer
    ), f"Offer missing price and base_price. Offer: {offer}"
    assert (
        "seller_product_url" in offer
    ), f"Offer missing seller_product_url. Offer: {offer}"
