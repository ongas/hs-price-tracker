Feature: Parse and Display Product Information from BuyWisely
  As a Home Assistant user
  I want the integration to extract and display product information from BuyWisely product pages
  So that I can see all relevant details for the products I am tracking

  Scenario: Parse and display product details
    Given I have added a BuyWisely product to the price tracker
    When the system parses the product page
    Then the product's name, brand, image, price, and offers are extracted and shown to me
    And if parsing fails, I am notified or fallback logic is used
