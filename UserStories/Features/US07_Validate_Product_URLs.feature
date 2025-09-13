Feature: Validate BuyWisely Product URLs
  As a Home Assistant user
  I want the system to validate BuyWisely product URLs when I add them
  So that I am prevented from tracking invalid or malformed product links

  Scenario: Add a valid BuyWisely product URL
    Given I have a valid BuyWisely product URL
    When I add the product to the price tracker
    Then the product is accepted for tracking

  Scenario: Add an invalid BuyWisely product URL
    Given I have an invalid BuyWisely product URL
    When I try to add the product to the price tracker
    Then I receive a clear error message and the product is not tracked
