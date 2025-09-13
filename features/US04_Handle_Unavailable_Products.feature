Feature: Handle Unavailable or Deleted BuyWisely Products
  As a Home Assistant user
  I want to be notified or see when a BuyWisely product I am tracking becomes unavailable or is deleted
  So that I am aware that the product is no longer being tracked or cannot be purchased

  Scenario: Product becomes unavailable or deleted
    Given I am tracking a BuyWisely product
    When the product becomes unavailable or is deleted
    Then its status is set to 'deleted' or 'inactive'
    And the product is clearly marked as unavailable in the UI
    And I am informed of the change in status
