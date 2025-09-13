Feature: Support Multiple Offers for a BuyWisely Product
  As a Home Assistant user
  I want the integration to handle and display multiple offers for a single BuyWisely product
  So that I can understand the range of prices and sellers available for that product

  Scenario: Display multiple offers for a product
    Given a BuyWisely product has multiple offers
    When I view the product details
    Then up to 10 offers are displayed, each with price and currency information
    And the lowest price is always selected for tracking
