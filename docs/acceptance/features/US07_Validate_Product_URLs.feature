Feature: Validate BuyWisely Product URLs
  As a Home Assistant user
  I want the system to validate BuyWisely product URLs when I add them
  So that I am prevented from tracking invalid or malformed product links, including those that are not direct seller links (e.g., buywisely.com.au product pages).

  Scenario: Add a valid BuyWisely product URL
    Given I have a valid BuyWisely product URL (not a buywisely.com.au product page)
    When I add the product to the price tracker
    Then the product is accepted for tracking

  Scenario: Add an invalid BuyWisely product URL
    Given I have an invalid BuyWisely product URL (e.g., a buywisely.com.au product page, an image link, or a malformed URL)
    When I try to add the product to the price tracker
    Then I receive a clear error message and the product is not tracked
