# User Story 1: Add a BuyWisely Product for Price Tracking

**As a** Home Assistant user,
**I want** to add a product from BuyWisely to my price tracker,
**so that** I can monitor its price and receive updates when the price changes or the product becomes unavailable.

## Acceptance Criteria
- User can input a BuyWisely product URL into the Home Assistant integration.
- The system validates the URL and extracts the product ID.
- The product is added to the tracked items list with its current price (which must be greater than 0.0), name, brand, image, and the seller_product_url from the lowest-priced offer (never from any fallback or hydration field). If the extracted price is 0.0, it indicates an extraction bug and the product should not be added as a valid entity.
- If the product is not found or the URL is invalid, the user receives an error message.
- The user can add multiple BuyWisely products, and each is tracked as a separate entity.

---
