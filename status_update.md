# Status Update: BuyWisely Multi-Product Support
**Date:** 2025-09-27

## Summary
- A bug was fixed that prevented adding more than one 'buywisely' product.
- The root cause was an incorrect unique ID generation for configuration entries.
- The fix involves creating a unique ID based on the product URL for each 'buywisely' entry.

## Key Actions Taken
- Modified `custom_components/price_tracker/components/setup.py` to change unique ID generation.
- Updated `price_tracker_developer_guide.md` to document the fix.

## Current Status
- **Resolved.** The issue is fixed, and multiple 'buywisely' products can be configured.

---

# Status Update: BuyWisely Hydration Parser Extraction Regression
**Date:** 2025-09-25

## Summary
- The previous regex-based cleaning logic for the BuyWisely parser was identified as brittle and the root cause of the parsing failures.
- A new, robust, state-aware parser (`robust_stateful_cleaner`) was designed, implemented, and has now been integrated into the main `price_tracker` component.
- The new parser successfully cleans the push block data, allowing `demjson3` to parse the product information without errors.
- The parsing issue is now resolved in the production code.

## Key Actions Taken
- Replaced the fragile chain of `re.sub` and `.replace` calls with a single, state-aware cleaning function.
- The new function programmatically iterates through the data, correctly handling string literals, escape sequences, and custom data formats.
- Successfully executed the updated diagnostic script, which confirmed that the data is now parsed correctly.
- Integrated the new `robust_stateful_cleaner` logic into the `custom_components/price_tracker/services/buywisely/hydration_parser.py` file.
- Updated the developer guide to reflect the new architecture.

## Latest Diagnostic Results (2025-09-25)
- The `diagnose_buywisely_pushblock_parser.py` script now runs successfully.
- The `robust_stateful_cleaner` function correctly cleans the raw data.
- The `demjson3` library successfully parses the cleaned data into a Python object.
- The final parsed object contains the complete and correct product information.

## Next Steps
- Run integration tests to ensure the new parsing logic works correctly within Home Assistant.
- Create a pull request for the `fix/robust-parser-logic` branch to merge the changes.

## Current Status
- **Resolved.** The core data parsing issue is resolved. The robust cleaning logic has been integrated into the production code and is ready for integration testing.

---
*This file is updated automatically as part of the BuyWisely extraction regression workflow.*
