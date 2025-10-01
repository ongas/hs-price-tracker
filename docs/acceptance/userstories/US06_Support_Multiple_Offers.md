# User Story 6: Support Multiple Offers for a BuyWisely Product

**As a** Home Assistant user,
**I want** the integration to handle and display multiple offers for a single BuyWisely product,
**so that** I can understand the range of prices and sellers available for that product.

## Acceptance Criteria
- The system extracts *current* offers per product from BuyWisely hydration data by:
  1. Filtering to offers with the maximum `created_at` timestamp (excluding historical offers)
  2. Limiting to the first 10 offers (initially visible offers)
  3. Ignoring all historical offers (older `created_at` timestamps)
- Each offer includes price (which must be greater than 0.0) and currency information. Zero-priced offers must be ignored. If all current offers are zero-priced, it indicates an extraction bug and an exception should be raised.
- The lowest price and its seller_product_url are always selected for tracking (no fallback logic), but other offers can be displayed if needed.

---
