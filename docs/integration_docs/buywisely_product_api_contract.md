# BuyWisely Product API/Data Contract

This document defines the expected structure and sample payloads for BuyWisely product and offers data as required by the price_tracker integration. It is intended to make implementation and testing fool-proof, and to serve as a reference for diagnostics and future maintenance.

## 1. Product Page Hydration Data (JSON)

### Example Payload
```json
{
  "props": {
    "pageProps": {
      "hydration": {
        "product": {
          "id": "123456",
          "name": "Motorola Moto G75 5G 256GB Grey with Buds",
          "brand": "Motorola",
          "image": "https://cdn.buywisely.com/images/123456.jpg",
          "offers": [
            {
              "price": 299.99,
              "currency": "USD",
              "seller_product_url": "https://buywisely.com/product/123456/offer/1",
              "seller": "BestSeller Inc.",
              "availability": "in_stock"
            },
            {
              "price": 319.99,
              "currency": "USD",
              "seller_product_url": "https://buywisely.com/product/123456/offer/2",
              "seller": "OtherSeller LLC",
              "availability": "in_stock"
            }
          ],
          "description": "Latest model with 5G and bundled buds."
        }
      }
    }
  }
}
```

### Field Descriptions
- `product.id` (string): Unique product identifier.
- `product.name` (string): User-friendly product name. This should be concise and human-readable, as a user would expect to see in a store or catalog. Do not use the full HTML <title> if it contains branding or marketing text.
- `product.brand` (string): Brand name.
- `product.image` (string): URL to product image.
- `product.offers` (array): List of offers for this product.
  - `price` (number): Price of the offer. Must be greater than 0.0.
  - `currency` (string): Currency code (e.g., "USD").
  - `seller_product_url` (string): URL to the seller's product offer (must be used for entity `url`).
  - `seller` (string): Seller name.
  - `availability` (string): Stock status (e.g., "in_stock").
- `product.description` (string): Product description.

## 2. Extraction & Mapping Rules
- Only 'current offers' (those visible above 'See n more history offers' on the BuyWisely product page) must be processed. History offers must be ignored.
- Offers with a price of 0.0 (zero) must be ignored. If, after filtering, all current offers have a price of 0.0, an exception must be raised to signal an extraction bug.
- The `offers` list must be robustly traversed, regardless of its nesting in the hydration data.
- The `url` field in the entity must always be set to the `seller_product_url` of the lowest-priced current offer.
- No fallback or alternative fields are to be used for the seller URL.
- If no current offers are present, the entity `url` must be empty and this must be logged.
- After selecting the lowest-priced current offer, the system must fetch the seller's product page and validate the price using a hybrid approach:
  1. **Extract all prices** from the seller page (JSON and HTML)
  2. **Normalize and match**: Create variants of the expected price (e.g., "399.99" → ["399.99", "399", "39999", "$399.99", "AUD 399.99"]) and check if any extracted price matches
  3. **Score matches by context**: For each matching price, score based on surrounding context:
     - High confidence: Multiple occurrences + product price context (classes like "product-price", near product title)
     - Medium confidence: Single occurrence + product price context
     - Low confidence: Single occurrence, no clear context
     - Reject: Found in non-product context (shipping, discounts, related products, "save $", "from $")
  4. **Decision**: Accept high/medium confidence matches. Log and investigate low confidence or mismatches.
  5. If there is a mismatch or extraction failure, a diagnostic error is logged with details about all extracted prices and their contexts.

## 3. Diagnostics
- Log the full hydration data, the offers list, all candidate `seller_product_url` values, and the final `url` set in the entity.
- Log extraction failures and missing/invalid data with clear error messages.

## 4. Edge Cases
- Zero-priced offers (must be ignored, or trigger an exception if all offers are zero).
- Offers list missing or empty.
- Offers present but missing `seller_product_url`.
- Malformed or unexpected hydration data structure.
- Multiple offers with the same price (choose the first in the list).

## 5. Sample Error Payloads

### Missing Offers
```json
{
  "props": {
    "pageProps": {
      "hydration": {
        "product": {
          "id": "123456",
          "name": "Motorola Moto G75 5G 256GB Grey with Buds",
          "brand": "Motorola",
          "image": "https://cdn.buywisely.com/images/123456.jpg",
          "offers": [],
          "description": "Latest model with 5G and bundled buds."
        }
      }
    }
  }
}
```

### Offer Missing seller_product_url
```json
{
  "props": {
    "pageProps": {
      "hydration": {
        "product": {
          "id": "123456",
          "name": "Motorola Moto G75 5G 256GB Grey with Buds",
          "brand": "Motorola",
          "image": "https://cdn.buywisely.com/images/123456.jpg",
          "offers": [
            {
              "price": 299.99,
              "currency": "USD",
              "seller": "BestSeller Inc.",
              "availability": "in_stock"
            }
          ],
          "description": "Latest model with 5G and bundled buds."
        }
      }
    }
  }
}
```

---
This contract must be updated if the BuyWisely site changes its hydration data structure or offer fields.