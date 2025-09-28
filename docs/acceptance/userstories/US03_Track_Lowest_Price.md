# User Story 3: Automatically Track the Lowest Price for a BuyWisely Product

**As a** Home Assistant user,
**I want** the integration to always track and display the lowest price available for a BuyWisely product,
**so that** I can be sure I am monitoring the best deal across all offers for that product.

## Acceptance Criteria
- The system parses all available offers for a product from BuyWisely, strictly using only the offers list in the hydration data.
- The lowest price and its corresponding seller_product_url are always selected and displayed (no fallback logic). Zero-priced offers must be ignored during this selection. If all current offers are zero-priced, it indicates an extraction bug and the product should be marked as inactive or an exception should be raised.
- If no offers are available, the product is marked as inactive or deleted.

---
