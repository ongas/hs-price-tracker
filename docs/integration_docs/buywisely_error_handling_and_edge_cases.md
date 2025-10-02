# BuyWisely Error Handling & Edge Case Catalog
## Definition of 'Initially Visible Offers'
The integration processes offers exactly as BuyWisely displays them in their UI (the "initially visible offers"). The selection pipeline is:

1. **Filter by timestamp**: Keep only offers with the maximum `created_at` timestamp (current offers, excluding historical)
2. **Sort using BuyWisely's display logic**:
   - Amazon offers first (sorted by total price among themselves)
   - Then all other offers (sorted by total price)
   - This matches BuyWisely's client-side JavaScript sorting
3. **Take first 10**: Select the first 10 offers from this sorted list (the "initially visible offers" shown before "View More")
4. **Apply domain filtering**: Remove offers matching user-configured excluded domains (using 'contains' matching)
5. **Price validation**: Validate prices on seller pages for remaining offers

Historical offers (those with older `created_at` timestamps) are automatically filtered out. This includes out-of-stock offers, stale prices, or any offer that BuyWisely marks as non-current in their JSON data. Only the initially visible offers (after domain filtering) are processed for seller page validation.

**Note on Affiliate Filtering**: We do NOT filter out affiliate offers because the JSON data's `shopback`/`cashrewards` fields do not reliably indicate which offers have affiliate disclosures on BuyWisely's UI. Users can exclude specific domains (like "amazon.com.au", "ebay.com.au") via the excluded_domains configuration if desired.


All error conditions and edge cases listed here are now handled by the robust, state-aware BuyWisely parser integrated in the price tracker component (see developer guide and user story 5).

This document catalogs all known error conditions, edge cases, and required diagnostics for the BuyWisely service integration. It is intended to ensure fool-proof, predictable, and diagnosable behavior.

---

## 1. Error Handling Principles
- All errors must be logged with clear, actionable messages.
- Diagnostics must include input data, attempted extraction steps, and final outcomes.
- Entity state must reflect extraction failures (e.g., empty url if no valid offer).
- No fallback or silent failure is permitted.

---

## 2. Edge Cases & Required Handling

### 2.1 Offers List Missing
- **Condition:** `product.offers` key is missing from hydration data.
- **Action:**
  - Log: "Offers list missing in hydration data for product {product.id}"
  - Set entity `url` to empty.

### 2.2 Offers List Empty
- **Condition:** `product.offers` is present but empty (`[]`), or all offers are history offers (not current).
- **Action:**
  - Log: "Current offers list empty for product {product.id}"
  - Set entity `url` to empty.

### 2.3 Offer Missing seller_product_url
- **Condition:** One or more offers are missing the `seller_product_url` field.
- **Action:**
  - Log: "Offer missing seller_product_url for product {product.id}, offer: {offer}"
  - Skip offers without `seller_product_url` when selecting lowest-priced offer.
  - If no valid offer remains, set entity `url` to empty and log.

### 2.4 Multiple Current Offers with Same Price
- **Condition:** Two or more current offers have the same lowest price.
- **Action:**
  - Log: "Multiple current offers with same lowest price for product {product.id}, using first occurrence."
  - Use the first current offer in the list.

### 2.5 Malformed Hydration Data
- **Condition:** Hydration data is not valid JSON, or expected keys are missing at any level.
- **Action:**
  - Log: "Malformed or missing hydration data for product URL: {url}"
  - Set entity `url` to empty.

### 2.6 HTTP/Network Errors (Transient/Unavailable)
- **Condition:** HTTP request fails, times out, or returns a non-200 status that is NOT 404 or 410.
- **Action:**
  - Log: "Network error or HTTP error {status_code} for product URL: {url}"
  - Set entity state to INACTIVE (unavailable).
  - Set entity name to "Unavailable {product_id}".

### 2.7 Product Page Not Found (Deleted)
- **Condition:** HTTP request returns 404 or 410 (Not Found or Gone).
- **Action:**
  - Log: "404/410 Not Found for product URL: {url}"
  - Set entity state to DELETED.
  - Set entity name to "Deleted {product_id}".

### 2.8 Zero-Priced Offers
- **Condition:** An offer has a `price` or `base_price` of 0.0.
- **Action:**
  - Log: "Zero-priced offer found for product {product.id}, offer: {offer}. Ignoring this offer."
  - Ignore this offer when determining the lowest price.
  - If, after ignoring zero-priced offers, no valid offers remain, raise an exception (e.g., `ValueError`) to signal an extraction bug.

### 2.9 Unexpected Data Types
- **Condition:** Fields are present but have unexpected types (e.g., price is string, offers is not a list).
- **Action:**
  - Log: "Unexpected data type for field {field} in product {product.id}"
  - Attempt to coerce if safe, else set entity `url` to empty.

### 2.10 Seller Page Price Validation
The system uses a hybrid approach to validate prices on seller pages:

#### 2.10.1 Price Extraction Failure
- **Condition:** Unable to extract any prices from the seller page.
- **Action:**
  - Log: "Price validation failed: Could not extract any prices from seller page {seller_product_url} for product {product.id}"
  - Accept the offer (BuyWisely data is trusted) but log for investigation.

#### 2.10.2 Price Not Found on Page
- **Condition:** Expected price not found among extracted prices (after normalization).
- **Action:**
  - Log: "Price validation failed: Expected price {expected_price} not found on seller page {seller_product_url}. Extracted prices: {all_prices}"
  - Skip this offer and try next offer.

#### 2.10.3 Price Found in Non-Product Context
- **Condition:** Expected price found but in non-product context (shipping, discounts, related products, "save $", "from $").
- **Action:**
  - Log: "Price validation uncertain: Found {expected_price} on seller page but context suggests it's not the product price. Context: {context_info}"
  - Skip this offer and try next offer.

#### 2.10.4 Low Confidence Match
- **Condition:** Expected price found once with no clear product price context.
- **Action:**
  - Log: "Price validation low confidence: Found {expected_price} once on seller page with no product price context. Accepting with warning."
  - Accept the offer but log for monitoring.

#### 2.10.5 High/Medium Confidence Match
- **Condition:** Expected price found multiple times OR found once in clear product price context.
- **Action:**
  - Log: "Price validation succeeded: Found {expected_price} on seller page with {confidence} confidence. Occurrences: {count}, Context: {context_info}"
  - Accept the offer.

---

## 3. Required Diagnostic Log Examples
- Log full hydration data on every extraction attempt.
- Log offers list and all candidate `seller_product_url` values.
- Log final selected `seller_product_url` and entity `url`.
- Log all error and edge case conditions as above.
- For price validation, log:
  - All extracted prices from seller page
  - Normalized variants of expected price
  - Matching prices with their contexts (HTML classes, surrounding text)
  - Confidence score for each match
  - Final validation decision and reasoning

---

## 4. Summary Table
| Edge Case                        | Entity url | Log Message Example                                              |
|----------------------------------|------------|-----------------------------------------------------------------|
| Zero-priced offers               | empty (exception) | Zero-priced offer found for product 123456, offer: {...}. Ignoring. (or exception) |
|----------------------------------|-------------------|------------------------------------------------------------------------------------|
| Offers missing                   | empty             | Offers list missing in hydration data for product 123456                           |
| Current offers empty             | empty      | Current offers list empty for product 123456                             |
| Offer missing seller_product_url | empty      | Offer missing seller_product_url for product 123456, offer: {...}|
| Multiple lowest price (current)  | first      | Multiple current offers with same lowest price for product 123456, using first occurrence. |
| Malformed hydration data         | empty      | Malformed or missing hydration data for product URL: ...         |
| HTTP/network error (transient)   | unavailable (INACTIVE) | Network error or HTTP error 500 for product URL: ...             |
| 404/410 Not Found (deleted)      | deleted    | 404/410 Not Found for product URL: ...                           |
| Unexpected data type             | empty      | Unexpected data type for field price in product 123456           |
| Seller page price not found      | try next offer | Price validation failed: Expected price 299.99 not found on seller page https://... Extracted prices: [199.99, 12.00, 5.00] |
| Price in non-product context     | try next offer | Price validation uncertain: Found 299.99 but context suggests shipping/discount. Context: "Shipping from $299.99" |
| Low confidence price match       | accept with warning | Price validation low confidence: Found 299.99 once with no product context. Accepting. |
| High confidence price match      | accept | Price validation succeeded: Found 299.99 with HIGH confidence. Occurrences: 3, Context: class="product-price" |

---

This catalog must be updated as new edge cases or error conditions are discovered.