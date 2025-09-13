Feature: Add a BuyWisely Product for Price Tracking
  As a Home Assistant user
  I want to add a product from BuyWisely to my price tracker
  So that I can monitor its price and receive updates when the price changes or the product becomes unavailable

  Scenario: Add a valid BuyWisely product URL
    Given I have a valid BuyWisely product URL
    When I add the product to the price tracker
    Then the product is added to the tracked items list with its current price, name, brand, and image

  Scenario: Add an invalid BuyWisely product URL
    Given I have an invalid BuyWisely product URL
    When I try to add the product to the price tracker
    Then I receive an error message indicating the URL is invalid
