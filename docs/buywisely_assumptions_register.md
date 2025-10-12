# BuyWisely Integration - Assumptions Register

This document explicitly captures all assumptions, implied behaviors, and undocumented design decisions in the BuyWisely integration. These are not formally specified in user stories or acceptance criteria but are embedded in the implementation.

**Purpose**: Make implicit assumptions explicit to prevent misunderstandings, facilitate maintenance, and support future decision-making.

---

## 1. Data Source Assumptions

| ID | Assumption | Impact | Risk if Wrong | Verification Method |
|----|-----------|--------|---------------|---------------------|
| A-DS-001 | BuyWisely always uses NextJS with either self-hosted hydration or `__NEXT_DATA__` script tag | Core extraction logic depends on this | Complete failure if they switch frameworks | Monitor for extraction failures |
| A-DS-002 | BuyWisely's `created_at` timestamp reliably indicates offer recency/validity | Historical filtering relies on this | May exclude valid current offers or include stale ones | Compare with actual BuyWisely UI |
| A-DS-003 | Offers with identical `created_at` (max timestamp) are all "current" | All offers with max timestamp are considered current | May include multiple offer batches if timestamps clash | Monitor for unexpected "current offer" counts |
| A-DS-004 | BuyWisely's JSON structure remains stable (offers array, seller object, price fields) | Parser depends on stable schema | Breaking changes would cause extraction failures | Version monitoring, schema validation |
| A-DS-005 | BuyWisely populates `shopback` and `cashrewards` fields ONLY for affiliate offers | Affiliate filtering relies on this | May incorrectly filter non-affiliate offers or miss affiliates | Spot-check filtered offers |
| A-DS-006 | BuyWisely's `base_price` and `shipping` fields are always numeric or numeric-parseable strings | Price calculations rely on this | Price calculation errors if non-numeric | Type validation in code |
| A-DS-007 | BuyWisely provides complete offer data in initial page load (no lazy loading beyond initial view) | No additional API calls needed | May miss offers loaded via AJAX/infinite scroll | Compare offer counts with UI |
| A-DS-008 | BuyWisely's `seller_product_url` always points to a valid, accessible product page | URL validation and price verification depend on this | Broken links, 404s, incorrect seller pages | URL validation, price matching |
| A-DS-009 | Out-of-stock offers have older `created_at` timestamps (not max) | Out-of-stock filtering via timestamp | May show out-of-stock if BuyWisely doesn't update timestamps | User feedback, manual checks |
| A-DS-010 | BuyWisely updates `created_at` when offer availability/price changes | Current offer identification | Stale offers may appear current if not updated | Monitor timestamp changes |

---

## 2. Price Validation Assumptions

| ID | Assumption | Impact | Risk if Wrong | Verification Method |
|----|-----------|--------|---------------|---------------------|
| A-PV-001 | Top 10 lowest-priced offers are sufficient for finding a valid, verifiable price | We only validate 10 offers | May miss valid offer at position 11+ if all top 10 fail | Monitor validation failure rates |
| A-PV-002 | Seller pages always display product price as numeric text in HTML | Price extraction logic depends on this | Fails if price is in image, SVG, or dynamic JS | Test against various sellers |
| A-PV-003 | Finding price multiple times on seller page indicates high confidence | Confidence scoring relies on repetition | May give false confidence for pages with price lists | Context checking mitigates this |
| A-PV-004 | Price extraction failure is non-fatal and should try next offer | Validation loop continues on failure | May waste time on consistently failing sellers | Timeout and rate limiting |
| A-PV-005 | Seller pages remain accessible without authentication/bot detection | Direct HTTP requests work | Fails if sellers implement CAPTCHAs, bot detection | Monitor HTTP errors |
| A-PV-006 | Price shown on BuyWisely matches price on seller page (within rounding tolerance) | Validation logic | Mismatches may occur due to sales, discounts, dynamic pricing | Tolerance allows ±$0.10 variance |
| A-PV-007 | First valid offer (after validation) is acceptable, no need to validate all 10 | Stop at first valid | May miss better-priced offer if earlier validation falsely passes | Validation confidence checks |
| A-PV-008 | Currency symbols ($ € £) can be stripped safely for numeric comparison | Price normalization | Fails if currency mixing (e.g., USD vs AUD) | Currency detection needed |
| A-PV-009 | Seller pages have product price in main content (not just shipping/related products) | Context extraction logic | False positives from related product prices | Context filtering in place |
| A-PV-010 | 2-second timeout per seller page is sufficient | Performance vs completeness tradeoff | May miss slow-loading pages | Monitor timeout rate |

---

## 3. Domain Filtering Assumptions

| ID | Assumption | Impact | Risk if Wrong | Verification Method |
|----|-----------|--------|---------------|---------------------|
| A-DF-001 | 'Contains' matching is more user-friendly than exact matching for domain exclusion | Users can exclude "ebay.com.au" to match both "ebay.com.au" and "www.ebay.com.au" | May exclude unintended domains (e.g., "ebaystore.com.au") | User feedback, documentation clarity |
| A-DF-002 | Users want to exclude entire domains, not specific URL paths | Configuration only accepts domain strings | Users may want path-level filtering | Feature requests |
| A-DF-003 | Case-insensitive matching is expected and desired | "EBAY.COM.AU" matches "ebay.com.au" | None significant | User expectations |
| A-DF-004 | Domain extraction via `urlparse().netloc` is sufficient | Works for standard URLs | Fails for malformed URLs, relative URLs | URL validation catches this |
| A-DF-005 | Global excluded domains apply to ALL products (no per-product override to re-include) | Exclusion is additive only | Users cannot override global exclusions for specific products | Design decision, documented |
| A-DF-006 | Empty or whitespace-only domain strings should be ignored silently | No error, just skip invalid entries | Users may not notice typos | Validation logging |
| A-DF-007 | Domain filtering happens BEFORE price sorting (order matters) | Ensures cheapest excluded offers don't affect sort | None if pipeline is correct | Pipeline verification |

---

## 4. Configuration & UI Assumptions

| ID | Assumption | Impact | Risk if Wrong | Verification Method |
|----|-----------|--------|---------------|---------------------|
| A-UI-001 | Users prefer refresh interval in hours (not minutes) for product tracking | UI shows "refresh_interval_hours" | Users may want sub-hourly updates | Feature requests |
| A-UI-002 | 12-hour default refresh interval is reasonable for price tracking | Default value | May be too slow for flash sales, too fast for stable products | User feedback |
| A-UI-003 | Users understand "excluded_domains" as comma-separated string input | UI uses string field, not multi-select | Less user-friendly but simpler implementation | UI/UX feedback |
| A-UI-004 | Product URL slug is sufficient as entity ID (uniqueness) | Entity ID derived from URL | Collisions if BuyWisely reuses slugs | Monitor for duplicates |
| A-UI-005 | Users want entity name to match product title (not a custom name) | Entity name = product title from BuyWisely | Users may want custom names | Feature requests |
| A-UI-006 | One config entry = one tracked product (no bulk import) | Manual entry per product | Tedious for many products | Feature requests |
| A-UI-007 | Users will check logs for diagnostic information (not in-app notifications) | Errors logged, not surfaced in UI | Users may miss important errors | Error handling strategy |

---

## 5. Home Assistant Integration Assumptions

| ID | Assumption | Impact | Risk if Wrong | Verification Method |
|----|-----------|--------|---------------|---------------------|
| A-HA-001 | Sensor entity state should be the price value (numeric) | State is price, attributes contain URL and name | HA dashboards expect numeric state for graphs | HA conventions |
| A-HA-002 | Entity state should be set to UNAVAILABLE (not ERROR) on transient failures | Preserves last valid state | May confuse "unavailable" (temp) with "deleted" (permanent) | State differentiation |
| A-HA-003 | Entity attributes should include `url`, `product_name`, and `last_updated` | Standard attributes | Users may want more (seller name, confidence, etc.) | Feature requests |
| A-HA-004 | Entities are automatically updated on refresh interval (no manual update button in HA UI) | Polling-based updates | Users may want manual refresh | HA service call support |
| A-HA-005 | One sensor per product (not separate sensors for price, URL, name) | All data in one sensor | Alternative: separate sensors per attribute | Design decision |
| A-HA-006 | Price history tracking is HA's responsibility (via recorder), not integration's | No built-in history storage | Users need HA recorder configured | Documentation |
| A-HA-007 | Currency is dynamically determined based on offer data and seller domain, not always AUD. | Correct currency is displayed, enabling potential multi-currency support. | Incorrect currency display if detection logic fails or new domains are not mapped. | Dynamic currency detection and mapping. |

---

## 6. Performance & Scalability Assumptions

| ID | Assumption | Impact | Risk if Wrong | Verification Method |
|----|-----------|--------|---------------|---------------------|
| A-PS-001 | Users will track < 100 products (low-scale use case) | No optimization for high volume | Performance issues at scale | Monitor performance metrics |
| A-PS-002 | Sequential price validation (one seller page at a time) is acceptable | No parallel validation | Slow updates for multiple products | Update latency monitoring |
| A-PS-003 | 2-second timeout per seller page is sufficient | Balance speed vs completeness | May miss slow sites | Timeout rate monitoring |
| A-PS-004 | No rate limiting needed for BuyWisely API/pages | Unrestricted requests | May get blocked by BuyWisely or sellers | Monitor for 429 errors |
| A-PS-005 | Home Assistant can handle refresh intervals as low as 1 hour without performance issues | Minimum 1 hour in UI | More frequent updates could overwhelm system | System monitoring |
| A-PS-006 | Seller page HTML is small enough to parse in memory (< 5MB) | No streaming parsers | Memory issues for massive pages | Monitor memory usage |
| A-PS-007 | Network I/O is the bottleneck, not CPU for parsing | No heavy optimization needed | May need optimization at scale | Profile performance |

---

## 7. Error Handling & Resilience Assumptions

| ID | Assumption | Impact | Risk if Wrong | Verification Method |
|----|-----------|--------|---------------|---------------------|
| A-EH-001 | Transient HTTP errors (5xx) should not delete entities | Preserve entity state | Users see stale data during outages | Documented behavior |
| A-EH-002 | 404/410 errors indicate permanent deletion (not temporary unavailability) | Entity marked as "deleted" | False positives if temporary 404 | User feedback |
| A-EH-003 | Malformed JSON is a BuyWisely bug, not user error | Log and fail gracefully | Could be network corruption | Error rate monitoring |
| A-EH-004 | Price extraction failures are expected and normal (try next offer) | Non-fatal, loop continues | Constant failures may indicate systemic issue | Failure rate alerts |
| A-EH-005 | No retry logic needed for failed seller page requests | Single attempt per offer | May miss temporarily unavailable pages | Retry could improve success |
| A-EH-006 | Validation failures don't require user notification (just logging) | Silent failures | Users may not know validation is failing | Monitoring and alerts |
| A-EH-007 | Zero-priced offers are bugs/placeholders, not valid | Skip zero-priced offers | May exclude free items or pricing errors | Log for investigation |

---

## 8. Business Logic Assumptions

| ID | Assumption | Impact | Risk if Wrong | Verification Method |
|----|-----------|--------|---------------|---------------------|
| A-BL-001 | BuyWisely suggests the lowest total price (base_price + shipping), which then requires validation against the seller's page. | The system selects the lowest *verified* price after comparing BuyWisely's data with the actual seller's listing. | We might use an unverified or incorrect price if validation fails or is not performed. | Active validation against seller page; discrepancy logging. |
| A-BL-002 | Currencies are dynamically determined; conversion may be needed if the detected currency differs from the desired display currency. | Accurate currency display and potential for multi-currency support. | Incorrect currency display or conversion if detection/conversion logic fails. | Dynamic currency detection and conversion. |
| A-BL-003 | "Current offers" means max `created_at` timestamp, not "in stock" status | Filtering logic | Out-of-stock offers may appear if timestamps not updated | Timestamp accuracy |
| A-BL-004 | Affiliate offers (shopback/cashrewards) should be excluded by default | Automatic filtering | Users may want affiliate offers for cashback | Feature requests |
| A-BL-005 | First valid offer (after validation) is "good enough" | Stop at first valid | Doesn't validate all top 10 for absolute best | Optimization decision |
| A-BL-006 | Seller page price must match BuyWisely price (within tolerance) for trust | Validation logic | Could trust BuyWisely blindly | Trust model |
| A-BL-007 | Product name from BuyWisely is user-friendly (not raw HTML title) | Entity naming | May be too long, contain special chars | Name truncation/cleaning |
| A-BL-008 | Only product URL is needed (not additional product metadata like brand, category) | Minimal config | Users may want rich filtering/grouping | Feature requests |

---

## 9. Testing & Verification Assumptions

| ID | Assumption | Impact | Risk if Wrong | Verification Method |
|----|-----------|--------|---------------|---------------------|
| A-TV-001 | Unit tests with static JSON fixtures are sufficient (no live integration tests) | Fast tests, no external deps | May miss real-world API changes | Periodic manual testing |
| A-TV-002 | BDD acceptance tests simulate real scenarios adequately | Confidence in behavior | May miss edge cases not in test data | Test coverage analysis |
| A-TV-003 | Mock HTTP responses for seller page validation are representative | Test reliability | Real seller pages may behave differently | Spot-check real pages |
| A-TV-004 | Test data in `docs/acceptance/test_data/` covers all edge cases | Complete coverage | May miss rare edge cases | Coverage gaps analysis |
| A-TV-005 | Manual deployment verification is sufficient (no automated smoke tests in prod) | Catch issues before users | Issues may reach production | Monitoring and alerts |

---

## 10. Future Compatibility Assumptions

| ID | Assumption | Impact | Risk if Wrong | Verification Method |
|----|-----------|--------|---------------|---------------------|
| A-FC-001 | BuyWisely will not change their URL structure or domain | URL parsing and config rely on this | Would break all existing configs | Monitor for URL changes |
| A-FC-002 | BuyWisely will remain NextJS-based (or compatible framework) | Hydration extraction depends on this | Complete rewrite needed if they migrate | Framework detection |
| A-FC-003 | Seller websites will remain scrapeable (no universal bot protection) | Price validation depends on scraping | Would need headless browser or API access | Monitor validation failures |
| A-FC-004 | Home Assistant's entity model and config flow remain compatible | Integration depends on HA APIs | May break on HA major version upgrades | HA version compatibility testing |
| A-FC-005 | BuyWisely will not require authentication or API keys | Anonymous access assumed | Would need auth flow implementation | Monitor for auth requirements |

---

## 11. Operational Assumptions

| ID | Assumption | Impact | Risk if Wrong | Verification Method |
|----|-----------|--------|---------------|---------------------|
| A-OP-001 | Users run Home Assistant in a network environment with internet access | HTTP requests to BuyWisely and sellers | Fails in isolated networks | Documentation |
| A-OP-002 | Users' Home Assistant instances can make HTTPS requests to any domain | No proxy/firewall restrictions | Blocked by corporate/restrictive firewalls | Error handling and docs |
| A-OP-003 | No legal/ToS issues with scraping BuyWisely and seller pages for personal use | Integration is legal | Could violate ToS (unlikely for personal use) | Legal review |
| A-OP-004 | Users understand this is unofficial and not affiliated with BuyWisely | No official support expected | Misunderstanding of support expectations | Disclaimer in docs |
| A-OP-005 | Python dependencies (BeautifulSoup, requests, etc.) remain stable and compatible | Code relies on these libraries | Breaking changes in deps | Dependency pinning |

---

## Maintenance Notes

- **Review Frequency**: Quarterly or when major changes occur
- **Validation Process**: Check assumptions against user feedback, error logs, and BuyWisely API changes
- **Risk Assessment**: Regularly assess which assumptions have highest risk and add monitoring/validation
- **Documentation**: Update this register when new assumptions are discovered or existing ones change

---

**Last Updated**: 2025-10-02
**Next Review**: 2026-01-02

