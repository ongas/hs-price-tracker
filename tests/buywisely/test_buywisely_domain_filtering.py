"""
Tests for BuyWisely domain filtering functionality.

Tests cover:
- Domain extraction from seller_product_url
- Filtering offers based on excluded domains
- Global and per-product exclusion lists
- Edge cases (all filtered, none filtered, invalid URLs)
"""
import json
from pathlib import Path


# Domain extraction utility to be implemented in html_extractor
def extract_domain_from_url(url):
    """Extract domain from URL for filtering purposes."""
    from urllib.parse import urlparse
    if not url or not isinstance(url, str):
        return None
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower() if parsed.netloc else None
    except Exception:
        return None


def test_extract_domain_from_url():
    """Test domain extraction from various URL formats."""
    assert extract_domain_from_url("https://www.ebay.com.au/itm/123456") == "www.ebay.com.au"
    assert extract_domain_from_url("https://amazon.com.au/dp/ABC123") == "amazon.com.au"
    assert extract_domain_from_url("http://shop.local.com/product") == "shop.local.com"
    assert extract_domain_from_url("https://EBAY.COM.AU/test") == "ebay.com.au"  # lowercase
    assert extract_domain_from_url("not-a-url") is None
    assert extract_domain_from_url("") is None
    assert extract_domain_from_url(None) is None


def test_filter_offers_by_excluded_domains():
    """Test filtering offers based on excluded domain list."""
    # Load test data
    test_data_path = Path(__file__).parent.parent.parent / "docs" / "acceptance" / "test_data" / "buywisely" / "offers_multiple_domains.json"
    with open(test_data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    offers = data['offers']
    excluded_domains = ["www.ebay.com.au", "www.amazon.com.au"]

    # Filter offers
    filtered_offers = [
        offer for offer in offers
        if extract_domain_from_url(offer.get('seller_product_url')) not in excluded_domains
    ]

    # Should have 2 remaining offers (localretailer.com.au and techstore.com.au)
    assert len(filtered_offers) == 2
    assert filtered_offers[0]['seller']['name'] == "Local Retailer"
    assert filtered_offers[1]['seller']['name'] == "Tech Store Australia"


def test_filter_offers_all_excluded():
    """Test behavior when all offers are from excluded domains."""
    # Load test data
    test_data_path = Path(__file__).parent.parent.parent / "docs" / "acceptance" / "test_data" / "buywisely" / "offers_all_excluded_domains.json"
    with open(test_data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    offers = data['offers']
    excluded_domains = ["www.ebay.com.au", "www.amazon.com.au"]

    # Filter offers
    filtered_offers = [
        offer for offer in offers
        if extract_domain_from_url(offer.get('seller_product_url')) not in excluded_domains
    ]

    # Should have 0 remaining offers
    assert len(filtered_offers) == 0


def test_filter_offers_no_exclusions():
    """Test that no filtering occurs when excluded_domains is empty."""
    # Load test data
    test_data_path = Path(__file__).parent.parent.parent / "docs" / "acceptance" / "test_data" / "buywisely" / "offers_multiple_domains.json"
    with open(test_data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    offers = data['offers']
    excluded_domains = []

    # Filter offers
    filtered_offers = [
        offer for offer in offers
        if extract_domain_from_url(offer.get('seller_product_url')) not in excluded_domains
    ]

    # Should have all 4 offers
    assert len(filtered_offers) == 4


def test_filter_offers_case_insensitive():
    """Test that domain matching is case-insensitive."""
    # Load test data
    test_data_path = Path(__file__).parent.parent.parent / "docs" / "acceptance" / "test_data" / "buywisely" / "offers_multiple_domains.json"
    with open(test_data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    offers = data['offers']
    # Use uppercase in exclusion list
    excluded_domains = ["EBAY.COM.AU"]

    # Filter offers using 'contains' matching (case-insensitive)
    filtered_offers = []
    for offer in offers:
        domain = extract_domain_from_url(offer.get('seller_product_url'))
        if domain:
            domain_lower = domain.lower()
            is_excluded = any(excl.lower() in domain_lower for excl in excluded_domains)
            if not is_excluded:
                filtered_offers.append(offer)

    # Should exclude the eBay offer (contains ebay.com.au)
    assert len(filtered_offers) == 3
    assert all('ebay' not in offer['seller']['name'].lower() for offer in filtered_offers)


def test_filter_offers_contains_domain_match():
    """Test that 'contains' matching works for domain filtering."""
    offers = [
        {
            "seller_product_url": "https://ebay.com.au/item1",
            "seller": {"name": "Seller A"}
        },
        {
            "seller_product_url": "https://www.ebay.com.au/item2",
            "seller": {"name": "Seller B"}
        },
        {
            "seller_product_url": "https://ebay.com/item3",
            "seller": {"name": "Seller C"}
        },
        {
            "seller_product_url": "https://ebaystore.com.au/item4",
            "seller": {"name": "Seller D"}
        }
    ]

    # Use "ebay.com.au" - should match both ebay.com.au and www.ebay.com.au
    excluded_domains = ["ebay.com.au"]

    # Filter using 'contains' matching
    filtered_offers = []
    for offer in offers:
        domain = extract_domain_from_url(offer.get('seller_product_url'))
        if domain:
            is_excluded = any(excl in domain for excl in excluded_domains)
            if not is_excluded:
                filtered_offers.append(offer)

    # Should filter both "ebay.com.au" and "www.ebay.com.au" (both contain "ebay.com.au")
    # Should NOT filter "ebay.com" or "ebaystore.com.au"
    assert len(filtered_offers) == 2
    filtered_names = [o['seller']['name'] for o in filtered_offers]
    assert "Seller A" not in filtered_names  # ebay.com.au excluded
    assert "Seller B" not in filtered_names  # www.ebay.com.au excluded (contains ebay.com.au)
    assert "Seller C" in filtered_names      # ebay.com NOT excluded
    assert "Seller D" in filtered_names      # ebaystore.com.au NOT excluded


def test_filter_offers_missing_url():
    """Test handling of offers with missing or invalid seller_product_url."""
    offers = [
        {
            "seller_product_url": "https://valid.com/item1",
            "base_price": 100,
            "seller": {"name": "Valid Seller"}
        },
        {
            "seller_product_url": None,
            "base_price": 90,
            "seller": {"name": "No URL Seller"}
        },
        {
            "seller_product_url": "",
            "base_price": 95,
            "seller": {"name": "Empty URL Seller"}
        },
        {
            "seller_product_url": "not-a-valid-url",
            "base_price": 85,
            "seller": {"name": "Invalid URL Seller"}
        }
    ]

    excluded_domains = ["valid.com"]

    # Filter offers - offers with invalid URLs should have None domain
    filtered_offers = [
        offer for offer in offers
        if extract_domain_from_url(offer.get('seller_product_url')) not in excluded_domains
        and extract_domain_from_url(offer.get('seller_product_url')) is not None
    ]

    # Should have 0 valid remaining offers
    # - "valid.com" is excluded
    # - Others have None domain (invalid)
    assert len(filtered_offers) == 0


def test_filter_offers_combined_global_and_product():
    """Test combining global and per-product exclusion lists."""
    offers = [
        {
            "seller_product_url": "https://www.ebay.com.au/item1",
            "base_price": 100,
            "seller": {"name": "eBay"}
        },
        {
            "seller_product_url": "https://www.amazon.com.au/item2",
            "base_price": 110,
            "seller": {"name": "Amazon"}
        },
        {
            "seller_product_url": "https://temu.com/item3",
            "base_price": 90,
            "seller": {"name": "Temu"}
        },
        {
            "seller_product_url": "https://local.com.au/item4",
            "base_price": 105,
            "seller": {"name": "Local"}
        }
    ]

    global_excluded = ["www.ebay.com.au"]
    product_excluded = ["www.amazon.com.au", "temu.com"]

    # Combine exclusion lists
    all_excluded = set(global_excluded + product_excluded)

    filtered_offers = [
        offer for offer in offers
        if extract_domain_from_url(offer.get('seller_product_url')) not in all_excluded
    ]

    # Should only have "local.com.au" remaining
    assert len(filtered_offers) == 1
    assert filtered_offers[0]['seller']['name'] == "Local"


def test_filter_with_lowest_price_selection():
    """Test that domain filtering is applied before lowest price selection."""
    offers = [
        {
            "seller_product_url": "https://www.amazon.com.au/item1",
            "base_price": 180,  # Lowest but excluded
            "shipping": 0,
            "seller": {"name": "Amazon"}
        },
        {
            "seller_product_url": "https://www.ebay.com.au/item2",
            "base_price": 190,  # Second lowest but excluded
            "shipping": 0,
            "seller": {"name": "eBay"}
        },
        {
            "seller_product_url": "https://local.com.au/item3",
            "base_price": 200,  # Lowest after filtering
            "shipping": 0,
            "seller": {"name": "Local Retailer"}
        },
        {
            "seller_product_url": "https://techstore.com.au/item4",
            "base_price": 210,
            "shipping": 0,
            "seller": {"name": "Tech Store"}
        }
    ]

    excluded_domains = ["www.amazon.com.au", "www.ebay.com.au"]

    # Filter offers
    filtered_offers = [
        offer for offer in offers
        if extract_domain_from_url(offer.get('seller_product_url')) not in excluded_domains
    ]

    # Find lowest price among filtered offers
    if filtered_offers:
        lowest_offer = min(filtered_offers, key=lambda x: x['base_price'] + x['shipping'])
        assert lowest_offer['base_price'] == 200
        assert lowest_offer['seller']['name'] == "Local Retailer"


def test_validate_excluded_domains_config():
    """Test validation of excluded_domains configuration."""
    valid_domains = ["ebay.com.au", "amazon.com.au", "temu.com"]
    invalid_domains = ["", "  ", "http://test.com", "https://example.com/path"]

    def validate_domain(domain):
        """Validate a domain string for exclusion list."""
        if not domain or not isinstance(domain, str):
            return False
        # Strip whitespace
        domain = domain.strip()
        if not domain:
            return False
        # Should not contain protocol
        if domain.startswith(('http://', 'https://', '//')):
            return False
        # Should not contain path
        if '/' in domain:
            return False
        return True

    # Validate valid domains
    assert all(validate_domain(d) for d in valid_domains)

    # Validate invalid domains
    assert not any(validate_domain(d) for d in invalid_domains)

    # Filter to only valid domains
    mixed_list = valid_domains + invalid_domains
    valid_only = [d for d in mixed_list if validate_domain(d)]
    assert valid_only == valid_domains
