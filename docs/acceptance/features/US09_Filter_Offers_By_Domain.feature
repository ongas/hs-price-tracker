Feature: US09 - Filter Offers By Domain
  As a Home Assistant user tracking product prices
  I want to exclude offers from specific domains
  So that I only see prices from sellers I prefer and trust

  Background:
    Given the price_tracker integration is installed
    And the BuyWisely service is available

  Scenario: Global domain exclusion filters all products
    Given I configure global excluded_domains as:
      | domain         |
      | ebay.com.au    |
      | amazon.com.au  |
    When I add a BuyWisely product with offers from multiple domains
    Then offers from "ebay.com.au" are excluded
    And offers from "amazon.com.au" are excluded
    And offers from other domains are included
    And the lowest price is selected from remaining offers

  Scenario: Per-product domain exclusion filters only that product
    Given I add a BuyWisely product "Product A" with excluded_domains:
      | domain      |
      | temu.com    |
    And I add a BuyWisely product "Product B" with no excluded_domains
    When both products receive offers from "temu.com" and other domains
    Then "Product A" excludes "temu.com" offers
    And "Product B" includes all offers including "temu.com"

  Scenario: Combined global and per-product exclusions
    Given I configure global excluded_domains as:
      | domain         |
      | ebay.com.au    |
    And I add a BuyWisely product with excluded_domains:
      | domain         |
      | amazon.com.au  |
    When the product receives offers from multiple domains
    Then offers from "ebay.com.au" are excluded (global)
    And offers from "amazon.com.au" are excluded (per-product)
    And offers from other domains are included
    And the lowest price is selected from remaining offers

  Scenario: Domain extracted correctly from seller_product_url
    Given I configure excluded_domains as:
      | domain         |
      | ebay.com.au    |
    When an offer has seller_product_url "https://www.ebay.com.au/itm/123456"
    Then the domain "www.ebay.com.au" is extracted
    But the domain does not match "ebay.com.au" exactly
    And the offer is NOT excluded

  Scenario: Exact domain matching required
    Given I configure excluded_domains as:
      | domain         |
      | ebay.com.au    |
    When offers have the following domains:
      | domain           |
      | ebay.com.au      |
      | ebay.com         |
      | www.ebay.com.au  |
      | ebaystore.com.au |
    Then only "ebay.com.au" offers are excluded
    And "ebay.com" offers are included
    And "www.ebay.com.au" offers are included
    And "ebaystore.com.au" offers are included

  Scenario: All offers filtered out by domain exclusion
    Given I configure excluded_domains as:
      | domain         |
      | ebay.com.au    |
      | amazon.com.au  |
    When a product has ONLY offers from "ebay.com.au" and "amazon.com.au"
    Then all offers are excluded by domain filtering
    And the sensor state shows "no valid offers"
    And diagnostic logs indicate "all offers excluded by domain filter"

  Scenario: Empty exclusion list applies no filtering
    Given I configure excluded_domains as an empty list
    When a product receives offers from any domains
    Then no domain filtering is applied
    And all offers are evaluated normally

  Scenario: No exclusion configuration applies no filtering
    Given I do not configure excluded_domains at all
    When a product receives offers from any domains
    Then no domain filtering is applied
    And all offers are evaluated normally

  Scenario: Invalid domain entries are handled gracefully
    Given I configure excluded_domains as:
      | domain           | validity |
      | ebay.com.au      | valid    |
      |                  | invalid  |
      | http://test.com  | invalid  |
      | amazon.com.au    | valid    |
    When the configuration is validated
    Then warnings are logged for invalid entries
    And only "ebay.com.au" and "amazon.com.au" are used for filtering
    And offers from valid excluded domains are filtered
    And offers from invalid entries are not affected

  Scenario: Domain filtering applied after current offer filtering
    Given a product has both current and historical offers
    And I configure excluded_domains as:
      | domain         |
      | ebay.com.au    |
    When the product is processed
    Then historical offers are excluded first (existing logic)
    And domain filtering is applied only to remaining current offers
    And "ebay.com.au" offers among current offers are excluded

  Scenario: Domain filtering with lowest price selection
    Given I configure excluded_domains as:
      | domain         |
      | amazon.com.au  |
    When a product has offers:
      | seller             | price   | domain         |
      | Amazon             | $200.00 | amazon.com.au  |
      | eBay Store         | $250.00 | ebay.com.au    |
      | Local Retailer     | $220.00 | localshop.com  |
    Then the Amazon offer is excluded by domain
    And the lowest price is $220.00 (Local Retailer)
    And the seller_product_url is from Local Retailer

  Scenario: Malformed seller_product_url handled gracefully
    Given I configure excluded_domains as:
      | domain         |
      | ebay.com.au    |
    When an offer has malformed seller_product_url "not-a-valid-url"
    Then domain extraction fails
    And a warning is logged for the malformed URL
    And the offer is excluded due to validation failure

  Scenario: Case-insensitive domain matching
    Given I configure excluded_domains as:
      | domain         |
      | EBAY.COM.AU    |
    When an offer has domain "ebay.com.au"
    Then the domain matches (case-insensitive)
    And the offer is excluded

  Scenario: Duplicate domains in configuration
    Given I configure global excluded_domains as:
      | domain         |
      | ebay.com.au    |
    And I configure per-product excluded_domains as:
      | domain         |
      | ebay.com.au    |
    When a product receives offers from "ebay.com.au"
    Then the offers are excluded once (no duplicate processing)
    And behavior is identical to single exclusion

  Scenario: Domain filtering with zero-price offers
    Given I configure excluded_domains as:
      | domain         |
      | amazon.com.au  |
    When a product has offers:
      | seller             | price   | domain         |
      | Amazon             | $0.00   | amazon.com.au  |
      | Local Retailer     | $220.00 | localshop.com  |
    Then the Amazon offer is excluded by zero-price validation (existing)
    And domain filtering is not applied to already-excluded offers
    And the lowest price is $220.00 (Local Retailer)

  Scenario: Domain filtering generates diagnostic logs
    Given I configure excluded_domains as:
      | domain         |
      | ebay.com.au    |
      | amazon.com.au  |
    And diagnostic logging is enabled
    When a product is processed with offers from multiple domains
    Then logs show "X offers excluded by domain filter"
    And logs list each excluded domain that matched
    And logs show final count of remaining offers after filtering
