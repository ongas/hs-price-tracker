# Status Update - BuyWisely Entity Extraction Regression (2025-09-23)

## Current Focus
- Entity extraction for BuyWisely is broken after the last set of changes. The Home Assistant entity now shows `name: UNKNOWN`, `price: 0.0`, and an empty URL, even though the data and site structure have NOT changed and this was working previously.

## Diagnosis
- The last set of changes were intended to augment the entity attribute data with `seller_product_url`, but have instead caused a regression that prevents all entity data from being correctly populated.
- Hydration data extraction is failing to find product data, and the fallback to BeautifulSoup is not extracting a price or product details, resulting in default/fallback values.
- This is NOT a data or site change issue. The regression is due to recent code changes, not external factors.
- Diagnostics confirm that the hydration and fallback logic are being triggered, but no valid product or offer data is being extracted.

## Status
- Regression confirmed. Entity extraction is broken in the deployed environment due to recent code changes.

## Next Steps
- Review and revert or fix the recent changes that broke entity data extraction.
- Ensure that augmenting the entity with `seller_product_url` does not interfere with the extraction of all other entity fields.
- Add regression tests to prevent this in the future.

## Notes
- The data and site structure have NOT changed. This is a code regression.
- All BuyWisely tests may pass locally, but real entity extraction is broken after deployment.