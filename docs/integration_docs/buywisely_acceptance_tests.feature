# language: en

Feature: BuyWisely Product Tracking Acceptance
  This feature file defines the acceptance criteria and scenarios for the BuyWisely service integration, covering all core and edge case behaviors as specified in the requirements and error catalog.

  Background:
    Given the BuyWisely integration is installed and configured in Home Assistant

  Scenario: Extract seller_product_url from lowest-priced offer
    Given a BuyWisely product page with multiple offers
    When the integration parses the product data
    Then the entity url is set to the seller_product_url of the lowest-priced offer
    And the full hydration data, offers list, and selected url are logged

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

  Scenario: Multiple offers with same lowest price
    Given a BuyWisely product page with multiple offers at the same lowest price
    When the integration parses the product data
    Then the entity url is set to the seller_product_url of the first such offer
    And a log message indicates multiple offers with the same price

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
