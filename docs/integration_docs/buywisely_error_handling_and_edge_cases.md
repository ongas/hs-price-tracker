# BuyWisely Error Handling & Edge Case Catalog


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
- **Condition:** `product.offers` is present but empty (`[]`).
- **Action:**
  - Log: "Offers list empty for product {product.id}"
  - Set entity `url` to empty.

### 2.3 Offer Missing seller_product_url
- **Condition:** One or more offers are missing the `seller_product_url` field.
- **Action:**
  - Log: "Offer missing seller_product_url for product {product.id}, offer: {offer}"
  - Skip offers without `seller_product_url` when selecting lowest-priced offer.
  - If no valid offer remains, set entity `url` to empty and log.

### 2.4 Multiple Offers with Same Price
- **Condition:** Two or more offers have the same lowest price.
- **Action:**
  - Log: "Multiple offers with same lowest price for product {product.id}, using first occurrence."
  - Use the first offer in the list.

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

### 2.8 Unexpected Data Types

### 2.7 Unexpected Data Types
- **Condition:** Fields are present but have unexpected types (e.g., price is string, offers is not a list).
- **Action:**
  - Log: "Unexpected data type for field {field} in product {product.id}"
  - Attempt to coerce if safe, else set entity `url` to empty.

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
| Offers missing                   | empty      | Offers list missing in hydration data for product 123456         |
| Offers empty                     | empty      | Offers list empty for product 123456                             |
| Offer missing seller_product_url | empty      | Offer missing seller_product_url for product 123456, offer: {...}|
| Multiple lowest price            | first      | Multiple offers with same lowest price for product 123456, using first occurrence. |
| Malformed hydration data         | empty      | Malformed or missing hydration data for product URL: ...         |
| HTTP/network error (transient)   | unavailable (INACTIVE) | Network error or HTTP error 500 for product URL: ...             |
| 404/410 Not Found (deleted)      | deleted    | 404/410 Not Found for product URL: ...                           |
| Unexpected data type             | empty      | Unexpected data type for field price in product 123456           |

---

This catalog must be updated as new edge cases or error conditions are discovered.