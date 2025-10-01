Feature: Parse and Display Product Information from BuyWisely
  As a Home Assistant user
  I want the integration to extract and display product information from BuyWisely product pages
  So that I can see all relevant details for the products I am tracking

  Scenario: Parse and display product details with robust parser
    Given I have added a BuyWisely product to the price tracker
    When the system parses the product page using the robust, state-aware parser
  Then the product's user-friendly name (not the full HTML <title>), brand, image, price (which must be greater than 0.0), and offers are extracted and shown to me
    And if the extracted price is 0.0, it indicates an extraction bug
    And all known edge cases (see error/edge case catalog) are handled
    And the seller URL is always extracted from the offers list (never from fallback or hydration fields)
    And if parsing fails, I am notified with a clear diagnostic message
