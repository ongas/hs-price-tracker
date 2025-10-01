Feature: Support Multiple Offers for a BuyWisely Product
  As a Home Assistant user
  I want the integration to handle and display multiple offers for a single BuyWisely product
  So that I can understand the range of prices and sellers available for that product

  Scenario: Display multiple offers for a product
    Given a BuyWisely product has multiple offers
    When I view the product details
    Then only current offers (max created_at timestamp, first 10) are displayed, each with price greater than 0.0 and currency information
    And historical offers are ignored
    And zero-priced offers are ignored
    And the lowest price and its seller_product_url are selected for tracking
    And the price is rounded to 1 decimal place
