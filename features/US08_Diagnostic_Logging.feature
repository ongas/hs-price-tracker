Feature: Diagnostic Logging for BuyWisely Integration
  As a Home Assistant developer or advanced user
  I want detailed diagnostic logs for BuyWisely product tracking operations
  So that I can troubleshoot issues and verify correct operation of the integration

  Scenario: Generate diagnostic logs for product tracking
    Given the BuyWisely integration is running
    When a product is loaded, parsed, or data is extracted
    Then diagnostic logs are generated including product URLs, IDs, extracted data, and error messages
    And logs are accessible via the Home Assistant log system
