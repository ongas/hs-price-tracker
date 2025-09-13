Feature: View Tracked BuyWisely Product Details
  As a Home Assistant user
  I want to view the details of a BuyWisely product I am tracking
  So that I can see its current price, brand, name, image, and availability status

  Scenario: View details of a tracked BuyWisely product
    Given I have added a BuyWisely product to the price tracker
    When I view the tracked products list
    Then I see the product's name, brand, image, current price, and availability status
    And the product's tracked URL points to the lowest price offer available
