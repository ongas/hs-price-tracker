
import sys
import os
import json
import pytest


# Add the repository root to sys.path for robust import resolution
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../'))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from custom_components.price_tracker.services.buywisely.parser import parse_product

@pytest.fixture
def html_content():
    """Reads the content of the buywisely_fetched.html file."""
    file_path = os.path.join(os.path.dirname(__file__), 'buywisely_fetched.html')
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def test_buywisely_parser(html_content):
    """Tests the parse_product function for BuyWisely with comprehensive assertions."""
    # Parse the data
    parsed_data = parse_product(html_content)
    # Print the parsed data for debugging
    print(json.dumps(parsed_data, indent=2))
    # Assert that the data is a dictionary and not empty
    assert isinstance(parsed_data, dict)
    assert parsed_data
    # Assertions for specific fields
    assert parsed_data.get('title') == 'Motorola Moto G75 5G 256GB Grey with Buds'
    assert parsed_data.get('product_link') == 'https://www.buywisely.com.au/product/motorola-moto-g75-5g-256gb-grey-with-buds'
    assert parsed_data.get('brand') == 'Motorola'
    assert parsed_data.get('price') == 391.00
    assert parsed_data.get('currency') == 'AUD'
    assert parsed_data.get('availability') == 'In Stock'
    assert parsed_data.get('image') == 'https://buywisely.com.au/_next/image?url=https%3A%2F%2Fencrypted-tbn0.gstatic.com%2Fshopping%3Fq%3Dtbn%3AANd9GcTN0NDdrPCDIn9NaiVIb7vTMSRVKBOQbkBMTHJyb9dzqC_WY5IGMoYuvnsDtsI8XvfpsX50GHyVY5kvPm-1nSr2bXEkwcR1sLJr1IR1dAkwVcXTXGOCB8frf7o&w=640&q=75'
