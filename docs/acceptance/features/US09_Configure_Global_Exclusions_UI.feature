Feature: US09 - Configure Global Excluded Domains via UI
  As a Home Assistant user
  I want to configure global excluded_domains through the integration UI
  So that I can easily manage domain exclusions without editing YAML files

  Background:
    Given the price_tracker integration is installed
    And I am on the Home Assistant integrations page

  Scenario: Access integration options for global configuration
    Given the Price Tracker integration is set up
    When I navigate to Settings → Integrations
    And I click on "Price Tracker"
    And I click "Configure"
    Then I should see the integration options UI
    And I should see a field for "Global Excluded Domains (BuyWisely)"

  Scenario: Configure global excluded_domains via UI
    Given I am in the Price Tracker integration options
    When I enter "ebay.com.au,amazon.com.au" in the "Global Excluded Domains (BuyWisely)" field
    And I click "Submit"
    Then the configuration is saved
    And the integration reloads with the new configuration
    And all BuyWisely products now exclude offers from "ebay.com.au" and "amazon.com.au"

  Scenario: Update existing global excluded_domains via UI
    Given I have previously configured global excluded_domains as "ebay.com.au"
    When I open the integration options UI
    Then the "Global Excluded Domains (BuyWisely)" field shows "ebay.com.au"
    When I change it to "ebay.com.au,amazon.com.au,temu.com"
    And I click "Submit"
    Then the configuration is updated
    And all BuyWisely products now exclude the updated domain list

  Scenario: Clear global excluded_domains via UI
    Given I have previously configured global excluded_domains as "ebay.com.au,amazon.com.au"
    When I open the integration options UI
    And I clear the "Global Excluded Domains (BuyWisely)" field
    And I click "Submit"
    Then the global exclusions are removed
    And all BuyWisely products no longer filter by domain globally

  Scenario: UI shows help text for global excluded_domains
    Given I am in the Price Tracker integration options
    Then I should see help text explaining:
      """
      Enter comma-separated domain names to exclude from ALL BuyWisely products.
      Example: ebay.com.au,amazon.com.au,temu.com
      These exclusions apply globally to all products. Per-product exclusions can be set when adding products.
      """

  Scenario: Invalid domain format shows validation error
    Given I am in the Price Tracker integration options
    When I enter "http://ebay.com.au, , amazon.com.au" in the field
    And I click "Submit"
    Then the configuration is saved
    And invalid entries are automatically filtered out
    And only valid domains "amazon.com.au" are applied

  Scenario: Options UI configuration overrides YAML configuration
    Given I have configured in configuration.yaml:
      """
      price_tracker:
        buywisely:
          global_excluded_domains: "ebay.com.au"
      """
    When I configure via the UI with "amazon.com.au"
    Then the UI configuration takes precedence
    And only "amazon.com.au" is excluded globally
    And YAML configuration is ignored

  Scenario: Documentation link visible in integration UI
    Given the Price Tracker integration is set up
    When I view the integration in Settings → Integrations
    Then I should see a "Documentation" link
    When I click the documentation link
    Then I am taken to the integration documentation

  Scenario: Multiple services have separate global exclusion fields
    Given the price_tracker integration supports multiple services
    When I open the integration options UI
    Then I should see "Global Excluded Domains (BuyWisely)"
    And if other services are added, they should have separate fields
    And configuring one service's exclusions does not affect others
