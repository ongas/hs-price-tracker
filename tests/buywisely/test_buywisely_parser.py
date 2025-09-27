def test_hydration_parser_with_g85_product():
    """Test that the parser can extract data from the Motorola Moto G85 HTML payload."""
    import os
    fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'real_buywisely_motorola-moto-g85-5g-128gb-urban-grey-.html')
    with open(fixture_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    parsed_data = extract_and_parse_all_hydration_data(html_content)

    assert isinstance(parsed_data, list)
    assert len(parsed_data) > 0

    product_data = parsed_data[0]

    assert 'Motorola' in product_data.get('name', '') or 'motorola' in product_data.get('name', '').lower()

    offers = product_data.get('offers', [])
    assert len(offers) > 0

from custom_components.price_tracker.services.buywisely.hydration_parser import extract_and_parse_all_hydration_data

def test_hydration_parser_with_real_data():
    """Test that the new hydration parser can extract data from a real BuyWisely HTML fixture."""
    import os
    fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'real_buywisely_product.html')
    with open(fixture_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    parsed_data = extract_and_parse_all_hydration_data(html_content)

    assert isinstance(parsed_data, list)
    assert len(parsed_data) > 0

    product_data = parsed_data[0]
    print("[DIAG] product_data:", product_data)

    # Try to find the product name or title in various possible locations
    name = product_data.get('name')
    title = product_data.get('title')
    product_nested = product_data.get('product', {})
    name_nested = product_nested.get('name')
    title_nested = product_nested.get('title')

    print(f"[DIAG] name: {name}, title: {title}, name_nested: {name_nested}, title_nested: {title_nested}")

    expected_name = 'Motorola Moto G75 5G 256GB Grey with Buds'
    if name == expected_name or title == expected_name or name_nested == expected_name or title_nested == expected_name:
        pass
    else:
        raise AssertionError(f"Expected product name '{expected_name}' not found in any key. product_data: {product_data}")

    offers = product_data.get('offers', [])
    if not offers and 'product' in product_data:
        offers = product_data['product'].get('offers', [])
    print("[DIAG] offers:", offers)
    assert len(offers) > 0

    # Check that at least one offer has the expected seller
    print("[DIAG] offers[0]:", offers[0] if offers else None)
    found = any(
        (offer.get('seller') == 'VTech Industries') or
        (isinstance(offer.get('seller'), dict) and offer['seller'].get('name') == 'VTech Industries')
        for offer in offers if isinstance(offer, dict)
    )
    assert found, f"No offer found with seller 'VTech Industries'. Offers: {offers}"
