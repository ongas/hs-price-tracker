import pytest
from custom_components.price_tracker.services.buywisely.hydration_parser import extract_and_parse_all_hydration_data

@pytest.mark.asyncio
async def test_new_product_page_parsing():
    with open('/mnt/e/source/personal_repos/homeassistant/custom_components/price_tracker/new_product_page.html', 'r') as f:
        html = f.read()
    
    product_data = extract_and_parse_all_hydration_data(html)
    
    assert product_data is not None
    assert isinstance(product_data, list)
    assert len(product_data) > 0
    assert product_data[0]['title'] == 'Motorola Moto G85 5G 128GB (Urban Grey)'