# User Story 3: Automatically Track the Lowest Price for a BuyWisely Product

**As a** Home Assistant user,
**I want** the integration to always track and display the lowest price available for a BuyWisely product,
**so that** I can be sure I am monitoring the best deal across all offers for that product.

## Acceptance Criteria
- The system parses all available offers for a product from BuyWisely, strictly using only the offers list in the hydration data.
- The lowest price and its corresponding seller_product_url are always selected and displayed (no fallback logic). Zero-priced offers must be ignored during this selection. If all current offers are zero-priced, it indicates an extraction bug and the product should be marked as inactive or an exception should be raised.
- If no offers are available, the product is marked as inactive or deleted.
- After selecting the lowest-priced offer, the system must fetch the seller's product page and validate that the price displayed matches BuyWisely's stated price using a hybrid approach:
  1. Extract all prices from the seller page (JSON and HTML)
  2. Normalize the expected price into variants (e.g., "399.99" → ["399.99", "399", "39999", "$399.99", "AUD 399.99"])
  3. Match extracted prices against normalized variants
  4. Score matches by context to verify they're product prices (not shipping, discounts, or related products)
  5. Accept high/medium confidence matches; skip offer and try next for low confidence or non-product context matches
  6. Log comprehensive diagnostics including all extracted prices, normalized variants, matching prices with contexts, confidence scores, and final decision

---
