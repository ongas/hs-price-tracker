from custom_components.price_tracker.services.buywisely.data_transformer import transform_raw_product_data

def test_url_fallback_to_seller_product_url():
    # Simulate product data with no main url, but valid seller_product_url in offers
    product_id = "test-fallback-seller-url"
    item_url = "http://example.com/fallback-item-url"
    seller_url = "https://external-seller.com/product/123"
    raw_data = {
        "title": "Test Product Seller URL Fallback",
        "brand": "TestBrand",
        "availability": "In Stock",
        "offers": [
            {"base_price": 99.99, "currency": "AUD", "seller_product_url": seller_url},
            {"base_price": 120.00, "currency": "AUD", "seller_product_url": "https://another.com/other"}
        ],
        # No 'url' key here
    }
    result = transform_raw_product_data(raw_data, product_id, item_url)
    assert hasattr(result, "url"), "Result missing url attribute"
    assert result.url == seller_url, f"Expected url to fallback to seller_product_url, got {result.url}"
    assert result.name == "Test Product Seller URL Fallback"
    assert result.price.price == 99.99
    assert result.price.currency == "AUD"
