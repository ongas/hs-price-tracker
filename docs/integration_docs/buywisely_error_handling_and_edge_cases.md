# BuyWisely Error Handling & Edge Case Catalog
## Definition of 'Current Offer'
The 'current offers' are strictly defined as the list of seller product offers visible above the 'See n more history offers' selection on the BuyWisely product page. Only these offers are considered valid for price extraction, validation, and entity state. Historical or expired offers below this section must be ignored for all logic and diagnostics.


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

### 2.10 Seller Page Price Mismatch
- **Condition:** The price displayed on the seller's product page does not match BuyWisely's stated price for the lowest offer.
- **Action:**
  - Log: "Price mismatch detected for product {product.id} at seller page {seller_product_url}. BuyWisely price: {bw_price}, Seller page price: {seller_price}"
  - Mark product as 'price mismatch' in entity state/attributes.

---

## 3. Required Diagnostic Log Examples
- Log full hydration data on every extraction attempt.
- Log offers list and all candidate `seller_product_url` values.
- Log final selected `seller_product_url` and entity `url`.
- Log all error and edge case conditions as above.

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
| Seller page price mismatch       | price mismatch | Price mismatch detected for product 123456 at seller page https://... BuyWisely price: 299.99, Seller page price: 319.99 |

---

This catalog must be updated as new edge cases or error conditions are discovered.