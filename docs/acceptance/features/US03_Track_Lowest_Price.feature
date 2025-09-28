Feature: Automatically Track the Lowest Price for a BuyWisely Product
  As a Home Assistant user
  I want the integration to always track and display the lowest price available for a BuyWisely product
  So that I can be sure I am monitoring the best deal across all offers for that product

  Scenario: Track the lowest price among multiple offers
    Given a BuyWisely product has multiple offers
    When the product is tracked
    Then the lowest price (which must be greater than 0.0) and its corresponding seller_product_url are selected and displayed (no fallback logic). Zero-priced offers must be ignored during this selection. If all current offers are zero-priced, it indicates an extraction bug and the product should be marked as inactive or an exception should be raised.

  Scenario: Validate price on seller's product page after selecting lowest offer
    Given the lowest-priced offer and its seller_product_url have been selected
    When the system fetches the seller's product page
    Then the price displayed on the seller's page must match BuyWisely's stated price
    And if there is a mismatch, a diagnostic error is logged and the product is marked as 'price mismatch'

  Scenario: Product has only zero-priced offers
    Given a BuyWisely product has only current offers with a price of 0.0
    When the product is tracked
    Then an error is logged indicating an extraction bug (e.g., "Extracted price cannot be zero or less.")
    And the product is marked as inactive or an exception is raised

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
