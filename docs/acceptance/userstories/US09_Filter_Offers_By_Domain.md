# User Story US09: Filter Offers By Domain

**As a** Home Assistant user tracking product prices
**I want** to exclude offers from specific domains (e.g., marketplaces, untrusted sellers)
**So that** I only see prices from sellers I prefer and trust

---

## Acceptance Criteria

### AC1: Global Domain Exclusion Configuration
**Given** I am configuring the price_tracker integration
**When** I specify a list of excluded domains in the integration configuration
**Then** offers from those domains are excluded from ALL tracked products

### AC2: Per-Product Domain Exclusion Configuration
**Given** I am configuring a specific product sensor
**When** I specify a list of excluded domains for that product
**Then** offers from those domains are excluded ONLY for that specific product

### AC3: Combined Filtering (Global + Per-Product)
**Given** I have both global and per-product excluded domains configured
**When** the system processes offers for a product
**Then** offers are excluded if their domain matches EITHER the global OR per-product exclusion list

### AC4: Domain Extraction from seller_product_url
**Given** an offer with a seller_product_url
**When** the system extracts the domain for filtering
**Then** only the domain portion is extracted (e.g., "ebay.com.au" from "https://www.ebay.com.au/itm/123456")

### AC5: Contains Domain Matching
**Given** excluded_domains contains "ebay.com.au"
**When** an offer has seller_product_url with domain containing "ebay.com.au"
**Then** the offer is excluded
**And** this includes both "ebay.com.au" and "www.ebay.com.au" (contains matching)
**And** offers from "ebay.com" or "ebaystore.com.au" are NOT excluded (partial match doesn't count)

### AC6: No Offers After Filtering
**Given** all available offers match excluded domains
**When** the system processes the product
**Then** the sensor shows appropriate "no valid offers" state
**And** diagnostic logging indicates all offers were filtered out

### AC7: Filtering Applied to Current Offers Only
**Given** the hydration data contains both current and historical offers
**When** domain filtering is applied
**Then** only current offers (by created_at timestamp) are considered for filtering
**And** historical offers are already excluded by the existing logic

### AC8: Domain Filtering with Lowest Price Selection
**Given** multiple offers remain after domain filtering
**When** the system selects the lowest price
**Then** the lowest price is selected from the remaining (non-excluded) offers
**And** the corresponding seller_product_url is used

### AC9: Empty Exclusion List Behavior
**Given** no excluded domains are configured (empty list or not specified)
**When** the system processes offers
**Then** no domain filtering is applied
**And** all offers are evaluated normally

### AC10: Invalid Domain Configuration Handling
**Given** excluded_domains contains invalid entries (e.g., empty strings, invalid formats)
**When** the configuration is validated
**Then** invalid entries are logged as warnings
**And** only valid domain entries are used for filtering

---

## Business Rules

1. **Domain Extraction**:
   - Extract domain from `seller_product_url` using URL parsing
   - Include subdomain in the extracted domain (e.g., "www.ebay.com.au")
   - Use the netloc component of the parsed URL

2. **Domain Matching**:
   - Use 'contains' matching (case-insensitive)
   - If excluded domain string is contained in the extracted domain, exclude the offer
   - Example: "ebay.com.au" in excluded list will match both "ebay.com.au" and "www.ebay.com.au"
   - Non-example: "ebay.com.au" will NOT match "ebay.com" or "ebaystore.com.au"

3. **Filtering Priority**:
   - Domain filtering is applied AFTER filtering out:
     - Historical offers (by created_at timestamp)
     - Affiliate offers (shopback/cashrewards populated)
   - Domain filtering is applied BEFORE:
     - Price sorting (lowest to highest)
     - Taking top 10 offers for validation
     - Seller page price validation

4. **Configuration Validation**:
   - Excluded domains must be strings
   - Empty strings are invalid and ignored
   - Whitespace-only strings are invalid and ignored
   - Domains should not include protocols (http://, https://)
   - Domains should not include paths or query parameters

5. **Logging & Diagnostics**:
   - Log the total number of offers from BuyWisely JSON
   - Log the number of current offers (after created_at filtering)
   - Log the number of offers filtered out by domain
   - Log each excluded domain that caused filtering
   - Log final count of remaining offers after domain filtering

6. **Backward Compatibility**:
   - If excluded_domains is not configured, behavior is unchanged
   - Existing configurations continue to work without modification

---

## Edge Cases

1. **All Offers Filtered**:
   - If all current offers are excluded by domain filtering
   - Entity should show "no valid offers" state
   - Diagnostic log should indicate "all offers excluded by domain filter"

2. **Null or Missing seller_product_url**:
   - If an offer has no seller_product_url
   - Cannot extract domain for filtering
   - Offer should be excluded by existing validation logic (AC from US06)

3. **Malformed seller_product_url**:
   - If seller_product_url is not a valid URL
   - Domain extraction fails
   - Log warning and exclude the offer

4. **Case Sensitivity**:
   - Domain matching should be case-insensitive
   - "EBAY.COM.AU" should match "ebay.com.au"

5. **Duplicate Domains in Configuration**:
   - If the same domain appears in both global and per-product lists
   - Treat as single exclusion (no impact on behavior)

6. **Mixed Valid and Invalid Exclusions**:
   - If exclusion list contains mix of valid and invalid domains
   - Use only valid domains for filtering
   - Log warnings for invalid entries

---

## Examples

### Example 1: Global Exclusion Only
```yaml
price_tracker:
  excluded_domains:
    - ebay.com.au
    - amazon.com.au
```
Result: All products exclude eBay and Amazon offers

### Example 2: Per-Product Exclusion Only
```yaml
sensor:
  - platform: price_tracker
    name: "Product A"
    url: "https://buywisely.com.au/product/product-a"
    excluded_domains:
      - temu.com
```
Result: Product A excludes Temu offers, other products unaffected

### Example 3: Combined Global + Per-Product
```yaml
price_tracker:
  excluded_domains:
    - ebay.com.au

sensor:
  - platform: price_tracker
    name: "Product A"
    url: "https://buywisely.com.au/product/product-a"
    excluded_domains:
      - amazon.com.au
```
Result: Product A excludes BOTH eBay and Amazon offers

---

## Related User Stories

- **US01**: Add BuyWisely Product - Configuration entry point
- **US03**: Track Lowest Price - Filtering affects price selection
- **US06**: Support Multiple Offers - Domain filtering applies to offer processing
- **US08**: Diagnostic Logging - Domain filtering generates diagnostic logs

---

## Test Data Requirements

- Fixture with offers from multiple domains (ebay.com.au, amazon.com.au, regular retailers)
- Fixture where all offers are from excluded domains
- Fixture with malformed or missing seller_product_url values
- Configuration examples with global, per-product, and combined exclusions
