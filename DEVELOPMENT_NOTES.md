#
# Mock Test Data

## HTML Mock Files

- Only one HTML mock file is present: `tests/buywisely/mock_buywisely_page_many_offers.html`.
- This file is used by the BuyWisely parser tests (see `tests/buywisely/test_buywisely_parser.py`).
- No other mock HTML, JSON, or CSV test data files are present or required by the current engine/common tests.
- If additional mock data is needed for future engines or tests, place them in the `tests/` directory and document their usage here.

---
#
# Engine Test Refactor and Parameterization (2025-09-13)

## Unified Engine Test Structure

- Engine tests for Coupang, Kurly, Rankingdak, Smartstore, and SSG are now unified in a single parameterized test: `tests/common/test_engine_generic.py`.
	- This test uses `pytest.mark.parametrize` to run the same logic for each engine, reducing duplication and improving maintainability.
	- If a new engine is added, simply add a new parameter to the test.
- Redundant individual engine test files (e.g., `test_coupang_engine.py`, `test_kurly_engine.py`, etc.) have been removed.
- The test suite is designed to be easy to extend and maintain. All common logic should be placed in `tests/common/` and engine-specific logic in the parameterized test.

### Known Issues

- The Coupang engine test may fail due to external API restrictions (HTTP 403). This is not a code issue and can be safely ignored unless the API becomes accessible.

### How to Add a New Engine Test

1. Implement the new engine in the appropriate `custom_components/price_tracker/services/<engine>/engine.py`.
2. Add a new parameter to the `pytest.mark.parametrize` decorator in `tests/common/test_engine_generic.py` for the new engine and a representative item URL.
3. Run the test suite to ensure the new engine is covered.

---
Last updated: [Unified engine tests, removed redundant files, and updated documentation.]
# DEVELOPMENT NOTES: BuyWisely Service Refactoring

## Test Directory Organization (2025-09-13)

### Common Test Directory
- All tests that are shared across multiple services or are not specific to a single integration (e.g., config flow, setup, utility tests, and test fixtures) have been moved to `tests/common/`.
- This includes:
	- `test_config_flow.py`
	- `test_list.py`
	- `test_setup.py`
	- `conftest.py`
- Service-specific tests remain in the root of `tests/` or in their respective subdirectories (e.g., `tests/buywisely/`).
- This structure improves maintainability and clarity, making it easier to locate and update shared test logic.


## Summary
This document records the changes made to refactor the BuyWisely service integration for improved reliability and maintainability.

### 1. Replaced BeautifulSoup with Next.js Hydration Parser
- The previous implementation used a combination of BeautifulSoup and custom logic to parse the `__NEXT_DATA__` script from the BuyWisely product page. This was unreliable and prone to errors.
- The new implementation uses the `nextjs-hydration-parser` library, which is specifically designed for this purpose. This makes the parsing logic more robust and easier to maintain.

### 2. Removed Selenium Fallback
- The previous implementation included a fallback mechanism to use Selenium to render the page if the `__NEXT_DATA__` script was not found. This was a heavy-handed approach that was not always necessary.
- The new implementation removes the Selenium fallback, as the `nextjs-hydration-parser` is able to reliably extract the data from the initial HTML.

### 3. Consolidated Behave Step Definitions
- The `features/steps` directory contained multiple files with duplicate step definitions, which caused `behave.step_registry.AmbiguousStep` errors.
- All step definitions have been consolidated into a single `features/steps/buywisely_steps.py` file to remove the ambiguity and improve maintainability.

### 4. Modular Design
- The modular design of the `price_tracker` has been preserved, with a clear separation of concerns between the `engine`, `parser`, `html_extractor`, and `data_transformer` modules.

## Why These Changes Were Made
- The previous implementation was unreliable and difficult to maintain.
- The new implementation is more robust, reliable, and easier to maintain.
- The consolidation of the step definitions fixes the `AmbiguousStep` errors and improves the maintainability of the feature tests.