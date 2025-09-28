
Feature: Validate BuyWisely Product URLs
  As a Home Assistant user
  I want the system to validate BuyWisely product URLs when I add them
  So that I am prevented from tracking invalid or malformed product links, but BuyWisely product pages are accepted and tracked.

  Scenario: Add a valid BuyWisely product URL
    Given I have a valid BuyWisely product URL (e.g., a buywisely.com.au product page for a product)
    When I add the product to the price tracker
    Then the product is accepted for tracking

  Scenario: Add an invalid BuyWisely product URL
    Given I have an invalid BuyWisely product URL (e.g., an image link, a malformed URL, or a non-product page)
    When I try to add the product to the price tracker
    Then I receive a clear error message and the product is not tracked
