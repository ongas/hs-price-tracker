# BuyWisely Global Domain Exclusions - Current Implementation

## Status

**Current Implementation**: Per-product exclusions only
**Requirements**: US09 specifies both global and per-product exclusions
**Workaround**: Apply same exclusions to each product manually

## Background

US09 acceptance criteria specify:
- **AC1**: Global domain exclusion at integration level (applies to ALL products)
- **AC2**: Per-product domain exclusion (applies to specific product)
- **AC3**: Combined filtering (merge global + per-product)

## Current Workaround

To achieve "global" exclusion behavior with the current implementation:

1. When adding each product via Settings → Integrations → Price Tracker → Add Entry
2. In the `excluded_domains` field, enter the same comma-separated list for each product

**Example:**
```
Product 1: excluded_domains = "ebay.com.au,amazon.com.au"
Product 2: excluded_domains = "ebay.com.au,amazon.com.au"
Product 3: excluded_domains = "ebay.com.au,amazon.com.au"
```

## Future Implementation

To fully implement US09 AC1 (global exclusions), the following changes are needed:

### 1. Add Integration-Level Options

Create a global configuration entry that stores integration-wide settings:

```python
# In config_flow.py - Add to PriceTrackerOptionsFlowHandler
async def async_step_init(self, user_input=None):
    """Configure integration-level options including global excluded_domains."""
    if user_input is not None:
        # Store global_excluded_domains in hass.data
        return self.async_create_entry(title="", data=user_input)

    return self.async_show_form(
        step_id="init",
        data_schema=vol.Schema({
            vol.Optional("global_excluded_domains", default=""): str,
        })
    )
```

### 2. Pass Global Exclusions to Engine

Modify sensor setup to merge global and per-product exclusions:

```python
# In sensor.py or setup.py
global_excluded = hass.data.get(DOMAIN, {}).get("global_excluded_domains", "")
per_product_excluded = config_entry.data.get("excluded_domains", "")

# Parse and merge
global_list = [d.strip() for d in global_excluded.split(",") if d.strip()]
per_product_list = [d.strip() for d in per_product_excluded.split(",") if d.strip()]
merged_excluded = list(set(global_list + per_product_list))

# Pass merged list to engine
engine = BuyWiselyEngine(
    item_url=product_url,
    excluded_domains=merged_excluded,
    # ... other params
)
```

### 3. Update UI/UX

- Add "Configure" button to integration card for global settings
- Show both global and per-product exclusions in entity attributes
- Provide clear labels distinguishing global vs per-product in UI

## Testing

The following tests are already in place and will pass once implementation is complete:

- `test_merge_global_and_per_product_exclusions`
- `test_merge_with_duplicate_domains`
- `test_global_exclusions_only`
- `test_per_product_exclusions_only`
- `test_combined_global_and_per_product_exclusions`
- `test_empty_global_with_per_product_exclusions`
- `test_none_global_with_per_product_exclusions`

BDD scenarios in `US09_Filter_Offers_By_Domain.feature` also cover this functionality.

## References

- User Story: `docs/acceptance/userstories/US09_Filter_Offers_By_Domain.md`
- BDD Feature: `docs/acceptance/features/US09_Filter_Offers_By_Domain.feature`
- Tests: `tests/buywisely/test_buywisely_domain_filtering.py`
- Assumptions: `docs/buywisely_assumptions_register.md` (A-DF-005)
