from custom_components.price_tracker.services.buywisely.hydration_parser import _extract_raw_next_f_push_strings

def test_extract_raw_next_f_push_strings_basic():
    """Test extraction of raw __next_f.push strings from simple HTML."""
    html_content = """
    <html>
    <body>
        <script>
            self.__next_f.push([1,"key1:value1;key2:value2"]);
            self.__next_f.push([1,"key3:value3"]);
        </script>
    </body>
    </html>
    """
    expected_strings = [
        "key1:value1;key2:value2",
        "key3:value3"
    ]
    extracted_strings = _extract_raw_next_f_push_strings(html_content)
    assert extracted_strings == expected_strings

def test_extract_raw_next_f_push_strings_no_push_calls():
    """Test with HTML that contains no __next_f.push calls."""
    html_content = """
    <html>
    <body>
        <script>
            console.log("hello world");
        </script>
    </body>
    </html>
    """
    extracted_strings = _extract_raw_next_f_push_strings(html_content)
    assert extracted_strings == []

def test_extract_raw_next_f_push_strings_empty_html():
    """Test with empty HTML."""
    html_content = ""
    extracted_strings = _extract_raw_next_f_push_strings(html_content)
    assert extracted_strings == []

def test_extract_raw_next_f_push_strings_complex_payload():
    """Test with a more complex payload from problematic_json_string.txt."""
    with open('tests/buywisely/fixtures/nextjs_json_string.txt', 'r') as f:
        raw_content = f.read()
    
    html_content = f'''<html><body><script>{raw_content}</script></body></html>'''

    extracted_strings = _extract_raw_next_f_push_strings(html_content)
    assert len(extracted_strings) > 0
    # Further assertions can be added to check the content of extracted_strings
    # For now, just checking that it's not empty and contains expected patterns
    assert any("product" in s for s in extracted_strings)
    assert any("offers" in s for s in extracted_strings)
