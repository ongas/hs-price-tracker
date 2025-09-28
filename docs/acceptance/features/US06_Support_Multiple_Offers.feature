Feature: Support Multiple Offers for a BuyWisely Product
  As a Home Assistant user
  I want the integration to handle and display multiple offers for a single BuyWisely product
  So that I can understand the range of prices and sellers available for that product

  Scenario: Display multiple offers for a product
    Given a BuyWisely product has multiple offers
    When I view the product details
    Then *current* offers are displayed, each with price (which must be greater than 0.0) and currency information. Zero-priced offers must be ignored. If all current offers are zero-priced, it indicates an extraction bug and an exception should be raised.
  And the lowest price and its seller_product_url are always selected for tracking (no fallback logic)
