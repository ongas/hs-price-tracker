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
- `product.name` (string): Product name.
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
- After selecting the lowest-priced current offer, the system must fetch the seller's product page and validate that the price displayed matches BuyWisely's stated price. If there is a mismatch, a diagnostic error is logged and the product is marked as 'price mismatch'.

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