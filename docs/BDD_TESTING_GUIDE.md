# BDD Testing Guide for Price Tracker

This guide explains how to run and maintain Behavior-Driven Development (BDD) tests for the BuyWisely integration using the Behave framework.

## Overview

The BDD tests provide executable specifications that validate all user stories and acceptance criteria. They serve as:
- Living documentation of system behavior
- Regression test suite
- Acceptance test validation
- Communication tool between developers and stakeholders

## Prerequisites

Ensure Behave and dependencies are installed:

```bash
conda activate homeassistant
pip install -r requirements.txt
```

Required packages:
- `behave` - BDD test framework
- `PyHamcrest` - Assertion library
- All project dependencies

## Project Structure

```
custom_components/price_tracker/
├── behave.ini                          # Behave configuration
├── docs/
│   └── acceptance/
│       ├── features/                   # Feature files (Gherkin)
│       │   ├── US01_Add_BuyWisely_Product.feature
│       │   ├── US02_View_BuyWisely_Product_Details.feature
│       │   ├── ...
│       │   ├── environment.py          # Test hooks and setup
│       │   ├── conftest.py            # Shared fixtures
│       │   └── steps/
│       │       └── buywisely_steps.py  # Step definitions
│       ├── test_data/                  # Test data fixtures
│       │   └── buywisely/
│       │       ├── valid_multiple_offers.json
│       │       └── ...
│       └── userstories/                # User story specifications
└── tests/
    └── buywisely/
        └── fixtures/                   # HTML fixtures
            └── real_buywisely_*.html
```

## Running BDD Tests

### Run All Tests

From the project root:

```bash
conda activate homeassistant
behave
```

### Run Specific Feature

```bash
behave docs/acceptance/features/US01_Add_BuyWisely_Product.feature
```

### Run Specific Scenario

```bash
behave docs/acceptance/features/US01_Add_BuyWisely_Product.feature:6
```

(Line 6 is where the scenario starts)

### Run with Tags

Add tags to feature files or scenarios:

```gherkin
@smoke @us01
Scenario: Add a valid BuyWisely product URL
```

Then run:

```bash
behave --tags=@smoke        # Run only smoke tests
behave --tags=@us01         # Run only US01 tests
behave --tags=@us01,@us02   # Run US01 OR US02
behave --tags=@smoke --tags=@regression  # Run smoke AND regression
```

### Verbose Output

```bash
behave --verbose
behave --logging-level=DEBUG
```

### Stop on First Failure

```bash
behave --stop
```

### Dry Run (Check Step Definitions)

```bash
behave --dry-run
```

## Understanding Test Output

### Success Output
```
Feature: Add a BuyWisely Product for Price Tracking

  Scenario: Add a valid BuyWisely product URL
    Given I have a valid BuyWisely product URL ... passed in 0.001s
    When I add the product to the price tracker ... passed in 0.523s
    Then the product is added to the tracked items list ... passed in 0.002s

1 feature passed, 0 failed, 0 skipped
1 scenario passed, 0 failed, 0 skipped
3 steps passed, 0 failed, 0 skipped, 0 undefined
```

### Failure Output
```
Scenario: Add an invalid BuyWisely product URL
  Given I have an invalid BuyWisely product URL ... passed
  When I try to add the product to the price tracker ... passed
  Then I receive an error message indicating the URL is invalid ... FAILED

Assertion Failed: Error should be set
Expected: not none
     but: was None
```

## Writing New Step Definitions

### Step Definition Structure

```python
from behave import given, when, then
from hamcrest import assert_that, equal_to, greater_than

@given("I have a valid product")
def step_impl(context):
    """Setup preconditions."""
    context.product_url = "https://..."
    context.is_valid = True

@when("I perform an action")
async def step_impl(context):
    """Execute the action under test."""
    context.result = await perform_action(context.product_url)

@then("I expect an outcome")
def step_impl(context):
    """Verify the outcome."""
    assert_that(context.result, greater_than(0))
```

### Best Practices

1. **Use descriptive names**: Step text should read like natural language
2. **Keep steps focused**: Each step should test one thing
3. **Use context for state**: Share data between steps via `context`
4. **Use PyHamcrest assertions**: More readable than bare asserts
5. **Handle async**: Mark async steps with `async def`
6. **Add docstrings**: Document what each step does

### Common Assertions

```python
from hamcrest import (
    assert_that,
    equal_to,
    not_none,
    is_,
    greater_than,
    less_than,
    contains_string,
    empty,
    has_length,
)

# Equality
assert_that(actual, equal_to(expected))

# Null checks
assert_that(value, not_none())
assert_that(value, is_(None))

# Comparisons
assert_that(price, greater_than(0.0))
assert_that(count, less_than(10))

# Strings
assert_that(error_msg, contains_string("Invalid"))

# Collections
assert_that(offers, empty())
assert_that(products, has_length(2))

# Boolean
assert_that(is_valid, is_(True))
```

## Test Data and Fixtures

### Using HTML Fixtures

```python
fixture_path = context.fixtures_dir / "real_buywisely_product.html"
with open(fixture_path, encoding="utf-8") as f:
    html_content = f.read()
```

### Using JSON Test Data

```python
from docs.acceptance.features.conftest import load_test_data

test_data = load_test_data("valid_multiple_offers.json")
```

### Creating New Fixtures

1. Capture real HTML from BuyWisely product page
2. Save to `tests/buywisely/fixtures/`
3. Create corresponding JSON in `docs/acceptance/test_data/buywisely/`
4. Update feature files to reference new fixtures

## Debugging BDD Tests

### Enable Logging

```bash
behave --logging-level=DEBUG
```

### Add Print Statements

```python
@when("I add the product")
async def step_impl(context):
    print(f"[DEBUG] Product URL: {context.product_url}")
    context.result = await engine.load()
    print(f"[DEBUG] Result: {context.result}")
```

### Use pdb Debugger

```python
@when("I add the product")
async def step_impl(context):
    import pdb; pdb.set_trace()
    context.result = await engine.load()
```

### Check Context State

```python
@then("I verify the result")
def step_impl(context):
    print(f"Context attributes: {dir(context)}")
    print(f"Product URL: {getattr(context, 'product_url', 'NOT SET')}")
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: BDD Tests

on: [push, pull_request]

jobs:
  bdd-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Conda
        uses: conda-incubator/setup-miniconda@v2
        with:
          environment-file: environment.yml
      - name: Run BDD Tests
        run: |
          conda activate homeassistant
          behave --junit --junit-directory test-reports/
      - name: Publish Test Report
        uses: mikepenz/action-junit-report@v2
        if: always()
        with:
          report_paths: test-reports/*.xml
```

## Maintenance Guidelines

### When to Update BDD Tests

1. **New Feature**: Add new feature file and scenarios
2. **Requirement Change**: Update existing scenarios
3. **Bug Fix**: Add regression scenario
4. **Refactoring**: Ensure all scenarios still pass

### Traceability

Maintain traceability between:
- User stories (`docs/acceptance/userstories/`)
- BDD features (`docs/acceptance/features/`)
- Step definitions (`docs/acceptance/features/steps/`)
- Implementation code (`custom_components/`)
- Pytest tests (`tests/`)

Update the traceability matrix (`docs/integration_docs/buywisely_traceability_matrix.md`) when adding new scenarios.

### Code Review Checklist

- [ ] All new features have corresponding BDD scenarios
- [ ] Step definitions follow naming conventions
- [ ] Assertions use PyHamcrest
- [ ] Async steps are properly marked
- [ ] Test data fixtures are version-controlled
- [ ] Traceability matrix is updated
- [ ] All scenarios pass locally
- [ ] Documentation is updated

## Troubleshooting

### "No steps directory found"

Ensure `steps/` directory exists:
```bash
mkdir -p docs/acceptance/features/steps
```

### "Step definition not found"

Check that step text in `.feature` file exactly matches step definition:
```python
# Feature file
When I add the product to the price tracker

# Step definition
@when("I add the product to the price tracker")  # Must match exactly!
```

### "Module not found"

Ensure project root is in Python path (already handled in `environment.py` and `buywisely_steps.py`).

### "Async step not running"

Behave supports async steps natively. Ensure:
1. Step is defined with `async def`
2. Step is called with `await` if needed in other steps

### "Fixture not found"

Check fixture paths:
```python
# Correct
fixture_path = context.fixtures_dir / "filename.html"

# Incorrect
fixture_path = "filename.html"  # No directory context
```

## Additional Resources

- [Behave Documentation](https://behave.readthedocs.io/)
- [Gherkin Syntax Reference](https://cucumber.io/docs/gherkin/reference/)
- [PyHamcrest Documentation](https://pyhamcrest.readthedocs.io/)
- [BDD Best Practices](https://cucumber.io/docs/bdd/)

## Quick Reference

### Common Commands

```bash
# Run all tests
behave

# Run specific feature
behave docs/acceptance/features/US01_Add_BuyWisely_Product.feature

# Run with tags
behave --tags=@smoke

# Verbose output
behave --verbose

# Stop on first failure
behave --stop

# Dry run (check definitions)
behave --dry-run

# List all scenarios
behave --dry-run --no-skipped

# Generate JUnit XML
behave --junit --junit-directory reports/
```

### Context Attributes

Set in `environment.py` and `conftest.py`:

```python
context.project_root       # Path to project root
context.fixtures_dir       # Path to HTML fixtures
context.test_data_dir      # Path to JSON test data
context.product_url        # Current product URL
context.result             # Result of operations
context.error              # Error messages
context.offers             # Product offers
context.logs               # Captured logs
```

---

**Note**: Always run BDD tests in the `homeassistant` conda environment to ensure correct dependencies.
