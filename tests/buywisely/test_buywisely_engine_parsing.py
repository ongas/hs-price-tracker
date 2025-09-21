from custom_components.price_tracker.services.buywisely.parser import parse_product

def test_parse_product_no_image():
    html = (
        '<html><body><script id="__NEXT_DATA__" type="application/json">'
        '{"props":{"pageProps":{"product":{"title":"No Image Product","slug":"no-image-product","availability":"In Stock","offers":[{"base_price":75.00}]}}}}'
        '</script></body></html>'
    )
    result = parse_product(html)
    print("[DIAG] result:", result)
    assert result["image"] == "", f"Image mismatch: {result.get('image')}"

def test_html_extractor_import_and_basic_call():
    from custom_components.price_tracker.services.buywisely.html_extractor import extract_product_data_from_html
    html_content = "<html><body></body></html>"
    result = extract_product_data_from_html(html_content)
    print("[DIAG] result:", result)
    assert isinstance(result, dict), f"Type mismatch: {type(result)}"
    assert "title" not in result, f"Unexpected title: {result.get('title')}"
    assert "price" not in result, f"Unexpected price: {result.get('price')}"
    assert "url" not in result, f"Unexpected url: {result.get('url')}"