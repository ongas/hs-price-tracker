Feature: Handle Unavailable or Deleted BuyWisely Products
  As a Home Assistant user
  I want to be notified or see when a BuyWisely product I am tracking becomes unavailable or is deleted
  So that I am aware that the product is no longer being tracked or cannot be purchased


  Scenario: Product becomes unavailable due to network error
    Given I am tracking a BuyWisely product
    When a network error (timeout, connection error, or non-404/410 HTTP error) occurs while loading the product
    Then its status is set to 'inactive' (unavailable)
    And its name is prefixed with "Unavailable "
    And the product is clearly marked as unavailable in the UI
    And I am informed that the product is temporarily unavailable

  Scenario: Product price is extracted as zero
    Given I am tracking a BuyWisely product
    When the product's price is extracted as 0.0
    Then its status is set to 'inactive' (unavailable)
    And an appropriate error is logged (e.g., "Extracted price cannot be zero or less.")
    And if all current offers are zero-priced, an exception is raised

  Scenario: Product page returns 404 or 410 (deleted)
    Given I am tracking a BuyWisely product
    When the product page returns 404 or 410 (Not Found or Gone)
    Then its status is set to 'deleted'
    And its name is prefixed with "Deleted "
    And the product is clearly marked as deleted in the UI
    And I am informed that the product has been deleted or removed
