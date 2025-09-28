Feature: Add a BuyWisely Product for Price Tracking
  As a Home Assistant user
  I want to add a product from BuyWisely to my price tracker
  So that I can monitor its price and receive updates when the price changes or the product becomes unavailable

  Scenario: Add a valid BuyWisely product URL
    Given I have a valid BuyWisely product URL
    When I add the product to the price tracker
    Then the product is added to the tracked items list with its current price (which must be greater than 0.0), name, brand, image, and the seller_product_url from the lowest-priced offer
    And if the extracted price is 0.0, it indicates an extraction bug and the product should not be added as a valid entity
    And I can set the refresh interval for the product during the add flow
    And the refresh interval field is labeled "Refresh Interval (minutes)"
    And the refresh interval field has a default value of 30

  Scenario: Add an invalid BuyWisely product URL
    Given I have an invalid BuyWisely product URL
    When I try to add the product to the price tracker
    Then I receive an error message indicating the URL is invalid

  Scenario: Add a BuyWisely product with only zero-priced offers
    Given I have a BuyWisely product URL where all current offers have a price of 0.0
    When I try to add the product to the price tracker
    Then I receive an error message indicating an extraction bug (e.g., "Extracted price cannot be zero or less.")

  Scenario: Add a second valid BuyWisely product URL
    Given I have already added a valid BuyWisely product
    When I add a second, different valid BuyWisely product
    Then the second product is also added to the tracked items list
    And I have two tracked BuyWisely products
