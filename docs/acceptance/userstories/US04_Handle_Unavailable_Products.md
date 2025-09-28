# User Story 4: Handle Unavailable or Deleted BuyWisely Products

**As a** Home Assistant user,
**I want** to be notified or see when a BuyWisely product I am tracking becomes unavailable or is deleted,
**so that** I am aware that the product is no longer being tracked or cannot be purchased.


## Acceptance Criteria
- If a tracked product cannot be loaded due to a network error (e.g., timeout, connection error, or non-404/410 HTTP error), its status is set to 'inactive' (unavailable) and its name is prefixed with "Unavailable ".
- If a tracked product's price is extracted as 0.0, it indicates an extraction bug. The product's status should be set to 'inactive' (unavailable) and an appropriate error logged, or an exception raised if all offers are zero-priced.

- If a tracked product page returns 404 or 410 (Not Found or Gone), its status is set to 'deleted' and its name is prefixed with "Deleted ".

- The product is clearly marked as unavailable or deleted in the UI, according to the above distinction.

- The user is informed of the specific change in status (unavailable vs deleted).

---
