# Global Excluded Domains Configuration

## Overview

The Price Tracker integration supports **both global and per-product domain exclusions** for BuyWisely products (US09).

- **Global exclusions**: Apply to ALL BuyWisely products
- **Per-product exclusions**: Apply only to specific products
- **Combined**: Offers are excluded if they match EITHER global OR per-product lists

## Configuration

### Option 1: UI Configuration (Recommended)

Configure global exclusions through the Home Assistant UI:

1. Navigate to **Settings → Integrations**
2. Find **Price Tracker** (E-Commerce Integrator)
3. Click on **any product entry** (e.g., "https://buywisely.com.au/product/...")
4. Click the **⚙️ cog icon** (Configure button)
5. Select **"Global Settings"** from the menu
6. You will see currently excluded domains listed in the description
7. **To add a domain**:
   - Enter domain in "Add Excluded Domain" field (e.g., `ebay.com.au`)
   - Click Submit
   - The integration will reload and the domain will be added
8. **To remove a domain**:
   - Select domain from "Remove Excluded Domain" dropdown
   - Click Submit
   - The integration will reload and the domain will be removed

**Note**: Global settings are shared across ALL product entries for the same service type (e.g., all BuyWisely products). You can access this from any product's configuration menu.

### Option 2: YAML Configuration

Alternatively, configure global exclusions in your `configuration.yaml`:

```yaml
price_tracker:
  buywisely:
    global_excluded_domains:
      - ebay.com.au
      - amazon.com.au
      - temu.com
```

**Note**: UI configuration takes precedence over YAML configuration. If you configure via UI, the YAML setting will be ignored.

### Per-Product Excluded Domains

When adding a product via Settings → Integrations → Price Tracker → Add Entry:

1. Enter the product URL
2. In the `excluded_domains` field, enter comma-separated domains: `wish.com,aliexpress.com`

This will exclude offers from these domains for **only that specific product**.

### Combined Example

**configuration.yaml:**
```yaml
price_tracker:
  buywisely:
    global_excluded_domains:
      - ebay.com.au
      - amazon.com.au
```

**Product 1 config:**
- `excluded_domains`: `temu.com`
- **Effective exclusions**: `ebay.com.au`, `amazon.com.au`, `temu.com`

**Product 2 config:**
- `excluded_domains`: `` (empty)
- **Effective exclusions**: `ebay.com.au`, `amazon.com.au` (global only)

**Product 3 config:**
- `excluded_domains`: `amazon.com.au,wish.com`
- **Effective exclusions**: `ebay.com.au`, `amazon.com.au`, `wish.com` (amazon.com.au deduplicated)

## Domain Matching

Domains are matched using **case-insensitive "contains" matching**:

- Configuration: `ebay.com.au`
- Matches: `www.ebay.com.au`, `ebay.com.au`, `WWW.EBAY.COM.AU`
- Does NOT match: `ebay.com`, `ebaystore.com.au`

## Format

- **Format**: Comma-separated domain list
- **Example**: `ebay.com.au,amazon.com.au,temu.com`
- **Whitespace**: Automatically trimmed
- **Invalid entries**: Empty strings, protocols (http://), paths are ignored

## Logging

When configured, you'll see diagnostic logs showing the merging:

```
[DIAG][__init__.py] Global excluded_domains configured: ebay.com.au,amazon.com.au
[DIAG][sensor.py] Excluded domains - Global: ['ebay.com.au', 'amazon.com.au'], Per-product: ['temu.com'], Merged: ['ebay.com.au', 'amazon.com.au', 'temu.com']
```

## Testing

After configuration:
1. Restart Home Assistant to apply global configuration
2. Add/update products with per-product exclusions
3. Check entity attributes to see which offers are selected
4. Verify excluded domains are not appearing in selected offers

## Related Documentation

- User Story: `docs/acceptance/userstories/US09_Filter_Offers_By_Domain.md`
- Error Handling: `docs/integration_docs/buywisely_error_handling_and_edge_cases.md`
- BDD Feature: `docs/acceptance/features/US09_Filter_Offers_By_Domain.feature`
