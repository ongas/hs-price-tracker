
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

### Manual

1. Copy the `custom_components/price_tracker` directory to your Home Assistant `custom_components` folder.
2. Add the integration via the Home Assistant UI.
3. During setup, select your desired extraction method:
   - If you choose **Advanced extraction**, you must complete the following steps:

### Advanced Extraction Setup (crawl4ai/Playwright)
1. Ensure `playwright` and `crawl4ai` are listed in your `manifest.json` (already included).
2. After installing the integration, **run the following command in your Home Assistant environment**:
   ```
   playwright install
   ```
   This downloads the required browser binaries for Playwright.
3. If you skip this step, advanced extraction will fail and the integration will fall back to basic extraction. A clear error will be logged in Home Assistant.

## Manual

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

## Extraction Methods
- **Basic extraction (BeautifulSoup):** Fast, lightweight, and works out-of-the-box. May miss some data on complex sites.
- **Advanced extraction (crawl4ai/Playwright):** More accurate and robust, especially for dynamic sites. Requires additional setup.

## Supported Services
- **BuyWisely:** Supports both basic and advanced extraction (crawl4ai/Playwright).
- Other services: Currently only support basic extraction. Advanced support may be added in the future.

## Troubleshooting
- If you see log messages like:
  > Advanced crawl4ai extraction failed for URL ... Error: ... This usually means Playwright browser binaries are missing or not installed. Run 'playwright install' in your environment to resolve. Falling back to basic extraction.

  Follow the instructions and run `playwright install`.

## Uninstalling
- To remove browser binaries, you can delete the `.cache/ms-playwright` directory in your environment.

## Types
Some properties represent calculated results. There are conditions for delivery, specific characteristics of the item, etc.

### Inventory
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
