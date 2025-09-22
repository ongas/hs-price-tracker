
from custom_components.price_tracker.services.buywisely.hydration_parser import extract_and_parse_all_hydration_data

def test_hydration_parser_with_real_data():
    """Test that the new hydration parser can extract data from a real HTML payload."""
    with open('tests/buywisely/fixtures/nextjs_json_string.txt', 'r') as f:
        raw_content = f.read()
    
    html_content = f'''<html><body><script>{raw_content}</script></body></html>'''
    
    parsed_data = extract_and_parse_all_hydration_data(html_content)
    
    assert isinstance(parsed_data, list)
    assert len(parsed_data) > 0
    
    product_data = parsed_data[0]
    
    assert product_data.get('name') == 'Motorola Moto G75 5G 256GB Grey with Buds'
    
    offers = product_data.get('offers', [])
    assert len(offers) > 0
    
    # Check the first offer for the seller product url
    assert offers[0].get('seller_product_url') == 'https://www.mydeal.com.au/motorola-g75-5g-256gb-with-moto-buds-charcoal-grey-au-stock-6-8-full-hd-120hz-8gb-256gb-dual-sim-50mp-16mp-water-protection-5000mah-2year-warranty-14598762'
