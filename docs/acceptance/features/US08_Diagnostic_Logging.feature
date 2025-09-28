Feature: Diagnostic Logging for BuyWisely Integration
  As a Home Assistant developer or advanced user
  I want detailed diagnostic logs for BuyWisely product tracking operations
  So that I can troubleshoot issues and verify correct operation of the integration

  Scenario: Generate diagnostic logs for product tracking
    Given the BuyWisely integration is running
    When a product is loaded, parsed, or data is extracted
  Then diagnostic logs are generated including product URLs, IDs, extracted data, error messages, the full hydration data, offers list, all candidate seller_product_url values, and the final url set in the entity. Logs must also include messages when zero-priced offers are encountered and ignored, or when an exception is raised due to all offers being zero-priced.
    And logs are accessible via the Home Assistant log system
