
from custom_components.price_tracker.services.buywisely.hydration_parser import extract_and_parse_all_hydration_data

def test_hydration_parser_with_real_data():
    """Test that the new hydration parser can extract data from a real HTML payload."""
    with open('tests/buywisely/fixtures/real_buywisely_product.html', 'r') as f:
        html_content = f.read()
    
    parsed_data = extract_and_parse_all_hydration_data(html_content)
    
    assert isinstance(parsed_data, list)
    assert len(parsed_data) > 0
    
    product_data = parsed_data[0]
    
    assert product_data.get('name') == 'Motorola Moto G75 5G 256GB Grey with Buds'
    
    offers = product_data.get('offers', [])
    assert len(offers) > 0
    
    # Check the first offer for the seller
    assert offers[0].get('seller') == 'Amazon'
