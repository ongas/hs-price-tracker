# BDD Acceptance Tests

This directory contains Behavior-Driven Development (BDD) acceptance tests for the BuyWisely integration.

## Quick Start

```bash
# Activate conda environment
conda activate homeassistant

# Run all acceptance tests
behave

# Run specific user story
behave features/US01_Add_BuyWisely_Product.feature
```

## Directory Structure

```
acceptance/
├── README.md                    # This file
├── features/                    # BDD feature files (Gherkin)
│   ├── US01_Add_BuyWisely_Product.feature
│   ├── US02_View_BuyWisely_Product_Details.feature
│   ├── US03_Track_Lowest_Price.feature
│   ├── US04_Handle_Unavailable_Products.feature
│   ├── US05_Parse_Display_Product_Info.feature
│   ├── US06_Support_Multiple_Offers.feature
│   ├── US07_Validate_Product_URLs.feature
│   ├── US08_Diagnostic_Logging.feature
│   ├── environment.py           # Behave test hooks
│   ├── conftest.py             # Shared fixtures
│   └── steps/
│       └── buywisely_steps.py  # Step definitions
├── test_data/                   # JSON test fixtures
│   └── buywisely/
│       ├── valid_multiple_offers.json
│       ├── empty_offers_list.json
│       └── ...
└── userstories/                 # User story specifications
    ├── US01_Add_BuyWisely_Product.md
    └── ...
```

## Feature Files (Gherkin)

Feature files describe expected system behavior in natural language:

```gherkin
Feature: Add a BuyWisely Product for Price Tracking
  As a Home Assistant user
  I want to add a product from BuyWisely to my price tracker
  So that I can monitor its price

  Scenario: Add a valid BuyWisely product URL
    Given I have a valid BuyWisely product URL
    When I add the product to the price tracker
    Then the product is added to the tracked items list
```

## Step Definitions (Python)

Step definitions implement the Gherkin steps:

```python
@given("I have a valid BuyWisely product URL")
def step_impl(context):
    context.product_url = "https://www.buywisely.com.au/product/..."

@when("I add the product to the price tracker")
async def step_impl(context):
    engine = BuyWiselyEngine(item_url=context.product_url)
    context.result = await engine.load()

@then("the product is added to the tracked items list")
def step_impl(context):
    assert_that(context.result, not_none())
    assert_that(context.result.price.price, greater_than(0.0))
```

## Test Data

JSON fixtures for edge cases:

- `valid_multiple_offers.json` - Multiple offers scenario
- `empty_offers_list.json` - No offers available
- `all_offers_missing_seller_product_url.json` - Missing seller URLs
- `multiple_offers_same_price.json` - Tie-breaking scenario
- `malformed_hydration_data.json` - Parser resilience
- And more...

## User Stories

Detailed specifications for each feature:

- **US01**: Add BuyWisely Product
- **US02**: View Product Details
- **US03**: Track Lowest Price
- **US04**: Handle Unavailable Products
- **US05**: Parse Display Product Info
- **US06**: Support Multiple Offers
- **US07**: Validate Product URLs
- **US08**: Diagnostic Logging

## Running Tests

### All Tests
```bash
behave
```

### Specific Feature
```bash
behave features/US01_Add_BuyWisely_Product.feature
```

### With Verbose Output
```bash
behave --verbose
```

### Dry Run (Check Definitions)
```bash
behave --dry-run --no-skipped
```

### Stop on First Failure
```bash
behave --stop
```

## Test Coverage

- **18 scenarios** across 8 features
- **54 step definitions** implemented
- **8 user stories** fully covered

## Documentation

- **Comprehensive Guide**: `../BDD_TESTING_GUIDE.md`
- **Implementation Summary**: `../BDD_IMPLEMENTATION_SUMMARY.md`
- **Traceability Matrix**: `../integration_docs/buywisely_traceability_matrix.md`

## Adding New Tests

1. Write feature file in `features/`
2. Run `behave --dry-run` to get step snippets
3. Implement steps in `features/steps/buywisely_steps.py`
4. Add test data to `test_data/buywisely/` if needed
5. Update traceability matrix

## Debugging

```bash
# Enable debug logging
behave --logging-level=DEBUG

# Add breakpoints in step definitions
import pdb; pdb.set_trace()

# Print context state
print(f"Context: {dir(context)}")
```

## CI/CD Integration

Generate JUnit XML for CI systems:

```bash
behave --junit --junit-directory reports/
```

## Support

See `../BDD_TESTING_GUIDE.md` for comprehensive documentation, troubleshooting, and best practices.
