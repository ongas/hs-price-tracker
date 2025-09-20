from custom_components.price_tracker.utilities.hydration_parser import parse_nextjs_hydration_data

def test_hydration_parser_extracts_seller_url():
    """Test that the new hydration parser can extract a seller URL from Next.js hydration data."""
    html_content = '''
    <html>
        <body>
            <script id="__NEXT_DATA__" type="application/json">
                {
                    "props": {
                        "pageProps": {
                            "product": {
                                "title": "Test Product",
                                "offers": [
                                    {
                                        "base_price": 99.99,
                                        "seller_product_url": "https://seller.example.com/product-page"
                                    }
                                ]
                            }
                        }
                    }
                }
            </script>
        </body>
    </html>
    '''
    parsed_data = parse_nextjs_hydration_data(html_content)
    assert isinstance(parsed_data, list)
    assert len(parsed_data) > 0
    product_data = parsed_data[0]
    assert product_data.get("offers", [{}])[0].get("seller_product_url") == "https://seller.example.com/product-page"