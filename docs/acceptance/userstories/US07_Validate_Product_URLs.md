# User Story 7: Validate BuyWisely Product URLs

**As a** Home Assistant user,
**I want** the system to validate BuyWisely product URLs when I add them,
**so that** I am prevented from tracking invalid or malformed product links.

## Acceptance Criteria
- The system strictly validates the `item_url` provided by the user for tracking. This `item_url` must be a valid BuyWisely product page URL (e.g., `https://www.buywisely.com.au/product/example-product`).
- If the provided `item_url` is invalid (e.g., malformed, not a BuyWisely domain, or not a product page), the user receives a clear error message, and the product is not added for tracking.
- When extracting `seller_product_url` from the BuyWisely product page, the system ensures this URL is *not* a BuyWisely domain and is a valid external product link. If no valid `seller_product_url` is found, appropriate fallback or error handling occurs.
- Only valid product URLs (for `item_url`) are accepted for tracking, and only valid external seller URLs (for `seller_product_url`) are used for linking.

---
