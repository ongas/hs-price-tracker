Feature: Automatically Track the Lowest Price for a BuyWisely Product
  As a Home Assistant user
  I want the integration to always track and display the lowest price available for a BuyWisely product
  So that I can be sure I am monitoring the best deal across all offers for that product

  Scenario: Track the lowest price among multiple offers
    Given a BuyWisely product has multiple offers
    When the product is tracked
    Then the lowest price and its corresponding seller_product_url are selected and displayed (no fallback logic)

  Scenario: No offers available for a product
    Given a BuyWisely product has no available offers
    When the product is tracked
    Then the product is marked as inactive or deleted

  Scenario: Refresh interval is configurable for BuyWisely
    Given I am adding a BuyWisely product
    When I configure the product
    Then I can set the refresh interval and it is respected by the integration
    And the refresh interval field is labeled "Refresh Interval (minutes)"
    And the refresh interval field has a default value of 30
