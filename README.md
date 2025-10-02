# 🛒 E-Commerce Price Tracker for Home Assistant

This is a custom component for [Home Assistant](https://www.home-assistant.io/) to track prices of products from e-commerce websites. You can find prices of products from different e-commerce websites like Amazon, Flipkart, etc. This component uses [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) to scrape the prices of products from the websites.

## Installation

> 🚨　We do not recommend installing custom components directly from GitHub.

### HACS (Home Assistant Community Store)

1. Add custom repository to HACS:
   - Go to HACS page in Home Assistant.
   - Click on Integrations.
   - Click on the three dots in the top right corner.
   - Click on Custom repositories.
   - Add the URL of this repository

## Manual

You can add entity to your system by configure button in the integrations page. Upsert Item page requires URL of the product page which you want to track.

### Add e-commerce platform

1. Go to the integrations page in Home Assistant.
2. Click on the `Add Integration` button.
3. Search for `E-Commerce Price Tracker`.
4. Click on the integration and configure it.
5. Click on the `Submit` button.

### Add product

1. Click `Configure` button in the integration page.
2. Click on the `Add entity` button. Some provider may require device id.
3. Fill the form and click on the `Submit` button.





### Configurations

- `Product URL`: URL of the product page which you want to track.
- `Management Category Id`: Category Id of the product. Some providers support their own display categories.
- `Refresh interval`: Interval in seconds to refresh the price of the product.
- `Proxy URL`: URL of the proxy server to use for scraping the website. (Optional)
- `Excluded Domains`: List of domain names to exclude from price comparison (e.g., `["ebay.com.au", "amazon.com.au"]`). (Optional, BuyWisely only)

#### Domain Filtering (BuyWisely)

For BuyWisely products, you can exclude offers from specific domains to filter out sellers you don't trust.

##### Global Domain Exclusions (Recommended)

Configure global exclusions that apply to **ALL** BuyWisely products via the UI:

1. Go to **Settings → Integrations**
2. Find **Price Tracker** (E-Commerce Integrator)
3. Click on any product entry
4. Click the **⚙️ cog icon** (Configure)
5. Select **"Global Settings"**
6. Add/remove domains using the form

**Benefits:**
- Configure once, applies to all BuyWisely products
- Easy to manage via UI
- No YAML editing required
- Takes precedence over YAML configuration

##### Per-Product Domain Exclusions

You can also exclude domains for specific products when adding them:
- Enter comma-separated domains in the `excluded_domains` field
- Example: `ebay.com.au,amazon.com.au`

##### YAML Configuration (Alternative)

```yaml
price_tracker:
  buywisely:
    global_excluded_domains:
      - reebelo.com.au
      - ebay.com.au
      - amazon.com.au
```

**How domain matching works:**
- Case-insensitive "contains" matching
- `ebay.com.au` matches both `ebay.com.au` and `www.ebay.com.au`
- Excluded domains are filtered before lowest price selection

For detailed documentation, see: [Global Excluded Domains Configuration](docs/integration_docs/global_excluded_domains_configuration.md)

### Types

Some properties represent calculated results. There are conditions for delivery, specific characteristics of the item, etc.

#### Inventory

Inventory information is divided into three types: `In Stock`, `Out of Stock`, and `Almost out of stock`.

- `In Stock`: The product is in stock.
- `Out of Stock`: The product is out of stock.
- `Almost out of stock`: The product is almost out of stock.

Almost out of stock is determined by the number of products in stock. The number of products in stock is set to 10 by default, but you can change it in the configuration or automatically set it by the provider.

## TODO

- [ ] Support Proxy and enhance scraping performance

## License

MIT License, see [LICENSE](LICENSE).

### Inspiration, Thanks to 

- [https://github.com/oukene/naver_shopping](https://github.com/oukene/naver_shopping)
- [https://github.com/mahlernim/coupang_price/](https://github.com/mahlernim/coupang_price/)
