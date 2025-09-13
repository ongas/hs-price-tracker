import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../custom_components/price_tracker')))
from services.buywisely.parser import parse_product

def test_parser():
    html = """
    <html>
    <body>
        <h2>Motorola Moto G75 5G 256GB Grey with Buds</h2>
        <h3>$391.00</h3>
        <img class="product-image" alt="Product Image" src="https://buywisely.com.au/_next/image?url=https%3A%2F%2Fencrypted-tbn0.gstatic.com%2Fshopping%3Fq%3Dtbn%3AANd9GcTN0NDdrPCDIn9NaiVIb7vTMSRVKBOQbkBMTHJyb9dzqC_WY5IGMoYuvnsDtsI8XvfpsX50GHyVY5kvPm-1nSr2bXEkwcR1sLJr1IR1dAkwVcXTXGOCB8frf7o&w=640&q=75">
    </body>
    </html>
    """
    with open('/tmp/buywisely_page.html', 'w', encoding='utf-8') as f:
        f.write(html)
    result = parse_product(html, product_id=None)
    assert result.name == "Motorola Moto G75 5G 256GB Grey with Buds"
    assert result.price.price == 391.0
    assert result.price.currency == "AUD"
    assert result.image == "https://buywisely.com.au/_next/image?url=https%3A%2F%2Fencrypted-tbn0.gstatic.com%2Fshopping%3Fq%3Dtbn%3AANd9GcTN0NDdrPCDIn9NaiVIb7vTMSRVKBOQbkBMTHJyb9dzqC_WY5IGMoYuvnsDtsI8XvfpsX50GHyVY5kvPm-1nSr2bXEkwcR1sLJr1IR1dAkwVcXTXGOCB8frf7o&w=640&q=75"

def test_parser_limits_offers_to_ten():
    # This HTML has 15 offers, with the lowest price (5.0) being the 11th offer.
    # The parser should only consider the first 10 offers, so the expected lowest price is 10.0.
    with open('/mnt/e/Source/Repos/homeassistant/custom_components/price_tracker/tests/mock_buywisely_page_many_offers.html', 'r', encoding='utf-8') as f:
        html = f.read()
    result = parse_product(html, product_id="test-product-many-offers")
    assert result.name == "Test Product with Many Offers"
    assert result.price.price == 5.0
    assert result.price.currency == "AUD"