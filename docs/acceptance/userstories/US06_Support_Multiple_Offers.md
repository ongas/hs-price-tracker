# User Story 6: Support Multiple Offers for a BuyWisely Product

**As a** Home Assistant user,
**I want** the integration to handle and display multiple offers for a single BuyWisely product,
**so that** I can understand the range of prices and sellers available for that product.

## Acceptance Criteria
- The system extracts up to 10 offers per product from BuyWisely, strictly from the hydration data.
- Each offer includes price and currency information.
- The lowest price and its seller_product_url are always selected for tracking (no fallback logic), but other offers can be displayed if needed.

---
