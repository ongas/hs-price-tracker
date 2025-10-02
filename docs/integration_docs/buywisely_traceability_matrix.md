# BuyWisely Traceability Matrix

This matrix maps each requirement, user story, BDD scenario, and edge case to its corresponding code modules, test data, diagnostics, and documentation. It ensures full coverage and traceability for the BuyWisely service integration.

## Core Functionality

| Requirement / Scenario | User Story | BDD Feature | Code Module(s) | Test File(s) | Test Data / Fixture(s) | Diagnostics / Log(s) | Documentation |
|------------------------|------------|-------------|----------------|--------------|------------------------|----------------------|---------------|
| Add BuyWisely product via config flow | US01 | US01_Add_BuyWisely_Product.feature | config_flow.py, components/setup.py | test_buywisely_ha_integration.py | N/A (config flow) | Config flow logs, entity registration | US01_Add_BuyWisely_Product.md |
| Extract product details from HTML | US02, US05 | US02_View_BuyWisely_Product_Details.feature, US05_Parse_Display_Product_Info.feature | services/buywisely/html_extractor.py, json_extractor.py, json_parser_utils.py | test_buywisely_engine_basic_extraction.py, test_basic_product_parsing.py | valid_multiple_offers.json | Hydration extraction logs, product data logs | US02, US05, buywisely_product_api_contract.md |
| Display user-friendly product name | US05 | US05_Parse_Display_Product_Info.feature | html_extractor.py, data_transformer.py | test_basic_product_parsing.py | valid_multiple_offers.json | Product title extraction logs | US05, buywisely_product_api_contract.md |
| Track lowest price from multiple offers | US03, US06 | US03_Track_Lowest_Price.feature, US06_Support_Multiple_Offers.feature | html_extractor.py (_process_product_offers), data_transformer.py | test_buywisely_engine_offers_selection.py, test_buywisely_offers_edge.py | valid_multiple_offers.json, multiple_offers_same_price.json | Offer filtering logs, lowest price selection | US03, US06 |
| Validate product URLs | US07 | US07_Validate_Product_URLs.feature | html_extractor.py (_is_valid_seller_url) | test_buywisely_engine_url.py, test_data_transformer_urls.py | N/A (validation logic) | URL validation logs | US07 |
| Diagnostic logging at all stages | US08 | US08_Diagnostic_Logging.feature | All modules | test_buywisely_ha_integration.py | All test data | All diagnostic logs | US08, buywisely_deployment_verification_guide.md |

## Offer Filtering Pipeline

| Requirement / Scenario | Code Module(s) | Test File(s) | Test Data / Fixture(s) | Diagnostics / Log(s) | Documentation |
|------------------------|----------------|--------------|------------------------|----------------------|---------------|
| Filter historical offers (created_at timestamp) | html_extractor.py:400-421 | test_buywisely_engine_offers_selection.py | valid_multiple_offers.json | "TOTAL offers from BuyWisely JSON", "Filtered to current offers" | buywisely_error_handling_and_edge_cases.md:2-10 |
| Filter affiliate offers (shopback/cashrewards) | html_extractor.py:423-428 | test_buywisely_engine_offers_selection.py | valid_multiple_offers.json | Affiliate filtering logs | buywisely_error_handling_and_edge_cases.md |
| Filter offers by excluded domains | html_extractor.py:430-458 | test_buywisely_domain_filtering.py | offers_multiple_domains.json, offers_all_excluded_domains.json | Domain filtering logs, excluded offer logs | US09_Filter_Offers_By_Domain.md, US09_Filter_Offers_By_Domain.feature |
| Sort offers by total price (base_price + delivery) | html_extractor.py:460-475 | test_buywisely_engine_offers_selection.py | valid_multiple_offers.json | Price sorting logs | buywisely_error_handling_and_edge_cases.md:7 |
| Take top 10 lowest-priced offers | html_extractor.py:478 | test_buywisely_engine_offers_selection.py | valid_multiple_offers.json | "Take up to 10 lowest-priced" log | buywisely_error_handling_and_edge_cases.md:8 |

## Domain Filtering (US09)

| Requirement / Scenario | BDD Feature | Code Module(s) | Test File(s) | Test Data / Fixture(s) | Diagnostics / Log(s) | Documentation |
|------------------------|-------------|----------------|--------------|------------------------|----------------------|---------------|
| Global domain exclusion | US09_Filter_Offers_By_Domain.feature | config_flow.py, html_extractor.py | test_buywisely_domain_filtering.py | offers_multiple_domains.json | Domain filtering logs | US09_Filter_Offers_By_Domain.md:AC1 |
| Per-product domain exclusion | US09_Filter_Offers_By_Domain.feature | config_flow.py, html_extractor.py | test_buywisely_domain_filtering.py | offers_multiple_domains.json | Domain filtering logs | US09_Filter_Offers_By_Domain.md:AC2 |
| Combined filtering (global + per-product) | US09_Filter_Offers_By_Domain.feature | html_extractor.py:398 | test_buywisely_domain_filtering.py::test_filter_offers_combined_global_and_product | N/A (inline test) | Domain filtering logs | US09_Filter_Offers_By_Domain.md:AC3 |
| Domain extraction from seller_product_url | US09_Filter_Offers_By_Domain.feature | html_extractor.py:15-23 (_extract_domain_from_url) | test_buywisely_domain_filtering.py::test_extract_domain_from_url | N/A (inline test) | Domain extraction logs | US09_Filter_Offers_By_Domain.md:AC4 |
| Contains domain matching (case-insensitive) | US09_Filter_Offers_By_Domain.feature | html_extractor.py:438-439 | test_buywisely_domain_filtering.py::test_filter_offers_case_insensitive, test_filter_offers_contains_domain_match | N/A (inline test) | Domain matching logs | US09_Filter_Offers_By_Domain.md:AC5 |
| No offers after filtering | US09_Filter_Offers_By_Domain.feature | html_extractor.py | test_buywisely_domain_filtering.py::test_filter_offers_all_excluded | offers_all_excluded_domains.json | "all offers excluded" log | US09_Filter_Offers_By_Domain.md:AC6 |
| Domain filtering with lowest price selection | US09_Filter_Offers_By_Domain.feature | html_extractor.py | test_buywisely_domain_filtering.py::test_filter_with_lowest_price_selection | N/A (inline test) | Price selection after filtering | US09_Filter_Offers_By_Domain.md:AC8 |

## Price Validation Loop

| Requirement / Scenario | Code Module(s) | Test File(s) | Test Data / Fixture(s) | Diagnostics / Log(s) | Documentation |
|------------------------|----------------|--------------|------------------------|----------------------|---------------|
| Validate price on seller page (top 10 offers loop) | data_transformer.py | test_buywisely_price_validation_loop.py | N/A (mock responses) | Price validation logs | buywisely_error_handling_and_edge_cases.md:2.10 |
| Seller page price extraction failure | data_transformer.py | test_price_validation_hybrid.py | N/A (mock responses) | "Price validation failed: Could not extract" | buywisely_error_handling_and_edge_cases.md:2.10.1 |
| Price not found on seller page - try next offer | data_transformer.py | test_buywisely_price_validation_loop.py | N/A (mock responses) | "Expected price not found", "try next offer" | buywisely_error_handling_and_edge_cases.md:2.10.2 |
| Price found in non-product context - try next | data_transformer.py | test_price_validation_hybrid.py | N/A (mock responses) | "Price validation uncertain", "context suggests" | buywisely_error_handling_and_edge_cases.md:2.10.3 |
| Low confidence match - accept with warning | data_transformer.py | test_price_validation_hybrid.py | N/A (mock responses) | "Price validation low confidence" | buywisely_error_handling_and_edge_cases.md:2.10.4 |
| High/medium confidence match - accept | data_transformer.py | test_price_validation_hybrid.py | N/A (mock responses) | "Price validation succeeded" | buywisely_error_handling_and_edge_cases.md:2.10.5 |
| All top 10 offers fail validation - no valid price | data_transformer.py | test_buywisely_price_validation_loop.py::test_price_validation_loop_handles_no_matching_offer | N/A (mock responses) | "No valid price found after validation" | buywisely_error_handling_and_edge_cases.md |

## Edge Cases & Error Handling

| Requirement / Scenario | Code Module(s) | Test File(s) | Test Data / Fixture(s) | Diagnostics / Log(s) | Documentation |
|------------------------|----------------|--------------|------------------------|----------------------|---------------|
| Offers list missing | html_extractor.py | test_buywisely_missing_data.py | missing_offers_key.json | "Offers list missing" log | buywisely_error_handling_and_edge_cases.md:2.1 |
| Offers list empty or all historical | html_extractor.py | test_buywisely_missing_data.py | empty_offers_list.json | "Current offers list empty" log | buywisely_error_handling_and_edge_cases.md:2.2 |
| Offer missing seller_product_url | html_extractor.py | test_buywisely_missing_data.py | all_offers_missing_seller_product_url.json | "Offer missing seller_product_url" | buywisely_error_handling_and_edge_cases.md:2.3 |
| Multiple offers with same lowest price | html_extractor.py | test_buywisely_engine_offers_selection.py | multiple_offers_same_price.json | "Multiple offers with same lowest price" | buywisely_error_handling_and_edge_cases.md:2.4 |
| Malformed hydration data (invalid JSON) | html_extractor.py, json_extractor.py | test_buywisely_invalid_json.py, test_buywisely_malformed_html.py | malformed_hydration_data.json | "Malformed or missing hydration data" | buywisely_error_handling_and_edge_cases.md:2.5 |
| HTTP/Network errors (transient) | engine.py | test_buywisely_timeout.py | network_error_simulation.json | "Network error or HTTP error" | buywisely_error_handling_and_edge_cases.md:2.6, US04 |
| Product page not found (404/410) | engine.py | test_buywisely_graceful_failure.py | deleted_404_simulation.json | "404/410 Not Found" | buywisely_error_handling_and_edge_cases.md:2.7, US04 |
| Zero-priced offers | html_extractor.py, data_transformer.py | test_buywisely_engine_price_validation.py::test_price_must_be_greater_than_zero, test_buywisely_offers_edge.py | N/A (inline test) | "Zero-priced offer found, ignoring" | buywisely_error_handling_and_edge_cases.md:2.8 |
| Unexpected data types | html_extractor.py | test_buywisely_parser_granular.py | unexpected_data_type_in_offers.json | "Unexpected data type for field" | buywisely_error_handling_and_edge_cases.md:2.9 |

## Currency & Formatting

| Requirement / Scenario | Code Module(s) | Test File(s) | Test Data / Fixture(s) | Diagnostics / Log(s) | Documentation |
|------------------------|----------------|--------------|------------------------|----------------------|---------------|
| Parse Euro currency (€) format | data_transformer.py | test_euro_currency_parsing.py | N/A (inline test) | Currency parsing logs | N/A |
| Handle various currency formats | data_transformer.py | test_buywisely_currency_format.py | N/A (inline test) | Currency parsing logs | N/A |

## URL Fallback & Special Cases

| Requirement / Scenario | Code Module(s) | Test File(s) | Test Data / Fixture(s) | Diagnostics / Log(s) | Documentation |
|------------------------|----------------|--------------|------------------------|----------------------|---------------|
| Fallback to product page URL when no valid seller URL | html_extractor.py | test_buywisely_url_fallback.py | N/A (inline test) | "Using fallback product page URL" | buywisely_error_handling_and_edge_cases.md |
| Timeout and rate limiting handling | engine.py | test_buywisely_timeout.py | N/A (mock timeout) | Timeout logs | buywisely_error_handling_and_edge_cases.md:2.6 |

## Deployment & Integration

| Requirement / Scenario | Code Module(s) | Test File(s) | Test Data / Fixture(s) | Diagnostics / Log(s) | Documentation |
|------------------------|----------------|--------------|------------------------|----------------------|---------------|
| Home Assistant entity integration | components/setup.py, components/sensor.py | test_buywisely_ha_integration.py | N/A (HA test harness) | Entity registration, state update logs | buywisely_deployment_verification_guide.md |
| Config flow for product setup | config_flow.py | test_buywisely_ha_integration.py | N/A (config flow) | Config flow logs | US01_Add_BuyWisely_Product.md |
| Refresh interval configuration (hours -> minutes) | config_flow.py:143-148 | N/A | N/A | Config conversion logs | US01_Add_BuyWisely_Product.md |
| Excluded domains configuration UI | config_flow.py:89-90 | N/A | N/A | Config validation logs | US09_Filter_Offers_By_Domain.md |

## Key Implementation Notes

### Offer Processing Pipeline Order
1. **Extract all offers** from BuyWisely JSON hydration data
2. **Filter historical offers** - Keep only offers with max `created_at` timestamp
3. **Filter affiliate offers** - Remove offers with shopback/cashrewards populated
4. **Apply domain filtering** - Exclude offers matching excluded_domains (contains matching)
5. **Sort by total price** - Sort remaining offers by (base_price + delivery) ascending
6. **Take top 10** - Select 10 lowest-priced offers for validation
7. **Validate prices** - Loop through top 10, validate price on seller page, accept first valid
8. **Select final offer** - Use validated offer's seller_product_url as entity url

### Data Extraction Methods
- **Primary**: NextJS self-hosted hydration data (buildId-based)
- **Fallback**: `__NEXT_DATA__` script tag extraction (rarely used)

### Domain Filtering Matching Logic
- **Case-insensitive** 'contains' matching
- Example: `"ebay.com.au"` in exclusion list matches both `"ebay.com.au"` and `"www.ebay.com.au"`
- Non-example: `"ebay.com.au"` does NOT match `"ebay.com"` or `"ebaystore.com.au"`

---

**Last Updated**: 2025-10-02
**This matrix must be updated as requirements, code, or tests evolve.**
