# language: en

Feature: BuyWisely Product Tracking Acceptance
# Definition of 'Current Offer':
# The 'current offers' are strictly defined as the list of seller product offers visible above the 'See n more history offers' selection on the BuyWisely product page. Only these offers are considered valid for price extraction, validation, and entity state. Historical or expired offers below this section must be ignored for all logic and diagnostics.
  This feature file defines the acceptance criteria and scenarios for the BuyWisely service integration, covering all core and edge case behaviors as specified in the requirements and error catalog.

  Background:
    Given the BuyWisely integration is installed and configured in Home Assistant

  Scenario: Extract seller_product_url from lowest-priced current offer
    Given a BuyWisely product page with multiple current offers (offers visible above 'See n more history offers')
    When the integration parses the product data
    Then the entity url is set to the seller_product_url of the lowest-priced current offer
    And the full hydration data, current offers list, and selected url are logged

  Scenario: Offers list missing
    Given a BuyWisely product page with no offers key in hydration data
    When the integration parses the product data
    Then the entity url is empty
    And a log message indicates the offers list is missing

  Scenario: Offers list empty
    Given a BuyWisely product page with an empty offers list
    When the integration parses the product data
    Then the entity url is empty
    And a log message indicates the offers list is empty

  Scenario: Offer missing seller_product_url
    Given a BuyWisely product page where all offers lack seller_product_url
    When the integration parses the product data
    Then the entity url is empty
    And a log message indicates the missing seller_product_url

  Scenario: Multiple current offers with same lowest price
    Given a BuyWisely product page with multiple current offers at the same lowest price
    When the integration parses the product data
    Then the entity url is set to the seller_product_url of the first such current offer
    And a log message indicates multiple current offers with the same price

  Scenario: Malformed hydration data
    Given a BuyWisely product page with malformed or missing hydration data
    When the integration parses the product data
    Then the entity url is empty
    And a log message indicates malformed hydration data

  Scenario: HTTP/network error
    Given a network or HTTP error occurs when fetching the product page
    When the integration attempts to update
    Then the entity state is set to unavailable
    And a log message indicates the HTTP error

  Scenario: Unexpected data type in offers
    Given a BuyWisely product page where offers or price fields have unexpected types
    When the integration parses the product data
    Then the entity url is empty
    And a log message indicates the unexpected data type

  Scenario: Validate price on seller's product page after selecting lowest offer
    Given the lowest-priced offer and its seller_product_url have been selected
    When the system fetches the seller's product page
  Then the price displayed on the seller's page must match BuyWisely's stated price
  And if there is a mismatch, a diagnostic error is logged
  And the system must move onto the next lowest-priced current offer and repeat the validation process
  And if all current offers result in a price mismatch, the product is marked as 'price mismatch' and all attempted offers and prices are logged
