import pytest
from custom_components.price_tracker.services.buywisely.parser import parse_product


async def test_parse_product_no_image():
    html = (
        '<html><body><script id="__NEXT_DATA__" type="application/json">'
        '{"props":{"pageProps":{"product":{"title":"No Image Product","slug":"no-image-product","availability":"In Stock","offers":[{"base_price":75.00}]}}}}'
        "</script></body></html>"
    )
    result = await parse_product(html)
    print("[DIAG] result:", result)
    assert result["image"] == "", f"Image mismatch: {result.get('image')}"


@pytest.mark.asyncio
async def test_html_extractor_import_and_basic_call():
    from custom_components.price_tracker.services.buywisely.html_extractor import (
        extract_product_data_from_html,
    )

    html_content = "<html><body></body></html>"
    result = await extract_product_data_from_html(html_content)
    print("[DIAG] result:", result)
    assert isinstance(result, dict), f"Type mismatch: {type(result)}"
