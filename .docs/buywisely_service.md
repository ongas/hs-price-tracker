# Buywisely Service Internal Documentation

This document serves as an internal reference for the Home Assistant `buywisely` price tracker component.

## Overview

The `buywisely` service is designed to track product prices from the BuyWisely website. Unlike services that provide a formal API, this component operates by **web scraping** the BuyWisely website. This means it directly fetches the HTML content of product pages and then parses that HTML to extract relevant information such as product title, price, image, and availability.

## Key Components and Files

The core functionality of the `buywisely` service is distributed across several key files within the `custom_components/price_tracker` directory:

-   **`config_flow.py`**: Handles the configuration process within Home Assistant, allowing users to set up new Buywisely product trackers. It manages the input of product URLs and other settings.

-   **`services/buywisely/engine.py`**: Contains the `BuyWiselyEngine` class. It is responsible for:
    -   Making HTTP requests to the BuyWisely product URLs.
    -   Handling responses and passing the HTML content to the parser.
    -   Constructing `ItemData` objects from the parsed information.

-   **`services/buywisely/parser.py`**: Contains the `parse_product` function. This function is responsible for:
    -   Taking the raw HTML content of a BuyWisely product page as input.
    -   Utilizing `nextjs_hydration_parser` to extract structured data, and falling back to `BeautifulSoup` for robust parsing of various HTML elements.
    -   Extracting specific product details suchs as title, price, image, currency, availability, and brand.

-   **`components/buywisely/setup.py`**: Defines the `BuyWiselySetup` class, which integrates the `buywisely` service with the Home Assistant configuration entry system. It handles the mapping of user input from the config flow to the internal data structures.

## Web Scraping Considerations

Due to its reliance on web scraping, the `buywisely` service is inherently susceptible to changes in the BuyWisely website's HTML structure. Any significant changes to the website's layout or element IDs could potentially break the parsing logic in `parser.py`, leading to incorrect or missing data.

## Testing

To ensure the reliability of the `buywisely` service, the following test files are crucial:

-   **`tests/test_config_flow.py`**: Verifies the correct functioning of the configuration flow within Home Assistant.

-   **`tests/buywisely_retriever_test/test_buywisely_parser.py`**: Tests the `parse_product` function, ensuring it correctly extracts data from various HTML structures.

-   **`tests/test_buywisely_engine.py`**: Tests the `BuyWiselyEngine` class, covering its data retrieval, parsing orchestration, and error handling.

## Future Improvements

-   **Robustness to Website Changes**: Implement mechanisms to detect significant changes in the BuyWisely website's structure and alert developers, or explore more resilient parsing techniques (e.g., using visual recognition or more flexible selectors).
-   **Rate Limiting/Throttling**: Implement more sophisticated rate limiting or throttling mechanisms to avoid overwhelming the BuyWisely website and to prevent IP blocking.
-   **Error Reporting**: Enhance error reporting for parsing failures, providing more specific details about what went wrong during data extraction.

## Testing the Live Container via Home Assistant API

To test the `buywisely` service running in a live Home Assistant container, you can use the Home Assistant REST API.

**1. Home Assistant API Endpoint:**

The service can be triggered by calling the `homeassistant/turn_on` service with the `entity_id` of the `buywisely` service.

**2. Authentication:**

You will need a Home Assistant Long-Lived Access Token. You can generate this from your Home Assistant profile page.

**3. Example `curl` Command:**

Here's an example `curl` command to trigger the `buywisely` service. Replace `YOUR_HA_IP:8123` with your Home Assistant instance's IP address and port, and `YOUR_LONG_LIVED_ACCESS_TOKEN` with your actual token.

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_LONG_LIVED_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "sensor.buywisely_price_tracker"}' \
  http://YOUR_HA_IP:8123/api/services/homeassistant/turn_on
```

**Note:** The `entity_id` might vary based on your configuration. Check your Home Assistant Developer Tools -> States page for the correct `entity_id` of your `buywisely` sensor or integration.

### Interacting with the Buywisely Service via Home Assistant API

To programmatically interact with the Buywisely service entities in Home Assistant, you can use the Home Assistant REST API.

**1. Obtain a Long-Lived Access Token:**
   - In your Home Assistant UI, click on your profile picture (bottom left).
   - Scroll down to "Long-Lived Access Tokens".
   - Click "CREATE TOKEN", give it a name (e.g., "CLI Access"), and copy the token. This token is sensitive and should be treated like a password.

**2. Constructing the cURL Command:**
   Use the following template for GET requests to retrieve entity states. Replace `YOUR_API_TOKEN` with the token you generated, `YOUR_HA_INSTANCE_ADDRESS:PORT` with your Home Assistant instance's address and port (e.g., `localhost:8123`), and `YOUR_ENTITY_ID` with the specific entity ID you wish to query (e.g., `sensor.buywisely_current_price`).

   ```bash
   curl -X GET \
     -H "Authorization: Bearer YOUR_API_TOKEN" \
     -H "Content-Type: application/json" \
     http://YOUR_HA_INSTANCE_ADDRESS:PORT/api/states/YOUR_ENTITY_ID
   ```

**3. Finding the Correct Entity ID:**
   If you are unsure of the exact entity ID for a Buywisely service, you can find it in your Home Assistant UI:
   - Navigate to **Developer Tools** (the icon that looks like `< >`).
   - Click on the **States** tab.
   - Use the "Filter entities" search bar to look for entities related to "buywisely" or "price_tracker". The `entity_id` will be listed for each.

**Security Note:**
   Avoid hardcoding API tokens directly into scripts or sharing them. The `secrets.yaml` file is for Home Assistant's internal configuration and should not be parsed by external tools for token extraction. Always obtain tokens securely and manage them carefully.

**Example:**
To retrieve the state of the `sensor.price_buywisely_type_motorola_moto_g75_5g-256gb_grey_with_buds` entity:

```bash
curl -X GET \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  http://localhost:8123/api/states/sensor.price_buywisely_type_motorola_moto_g75_5g-256gb_grey_with_buds
```

### Understanding Product URLs and Price Line Items

It's important to distinguish between the URL that the Home Assistant `buywisely` component processes (which is a listing page) and the actual, unique product URL.

*   **Listing/Search Page URL (Processed by `buywisely` component):** The URL that the `buywisely` component uses as its input (e.g., `https://www.buywisely.com.au/product/motorola-moto-g75-5g-256gb-grey-with-buds`) is typically a **listing or search results page**. This page displays multiple "product price line items" that match a certain query or category. The Home Assistant entity's `url` attribute reflects this input URL that the component processed.

*   **Product Price Line Item:** Each item on this listing page represents a distinct product offering. It usually includes details like product name, price, and a button or link.

*   **Actual Product URL:** The URL associated with the button or link on a "product price line item" is the **actual, unique product page URL**. This is the page that provides comprehensive details about that specific product.

**Processing Strategy for Listing Pages:**
When processing a listing page, the objective is to:
1.  Identify and extract information from the "product price line items" displayed on that page.
2.  Crucially, extract the "actual product URL" associated with each line item.
3.  Limit the processing to the **first 10** relevant "product price line items" found on the page.

## Development and Deployment Workflow

To ensure consistent development, testing, and deployment of the `price_tracker` custom component, follow these steps:

1.  **Code Modification:** Implement necessary changes in the component's source code.
2.  **Local Testing (pytest):**
    *   Run unit and integration tests using `pytest` to verify functionality and prevent regressions.
    *   Navigate to the `custom_components/price_tracker` directory.
    *   Execute tests: `pytest`
3.  **Code Quality (Linting):**
    *   Ensure code adheres to project style and quality standards using `ruff`.
    *   Navigate to the `custom_components/price_tracker` directory.
    *   Execute linter: `ruff check .`
    *   *Note:* Adhere to existing project conventions for formatting, including indentation (tabs vs. spaces), as observed in surrounding code.
4.  **Deployment:**
    *   Use the provided deployment script to copy updated files to the Home Assistant Docker configuration.
    *   Navigate to the `custom_components/price_tracker/` directory.
    *   Execute the deployment script: `./DEPLOYMENT_SCRIPT.sh`
5.  **Home Assistant Restart:**
    *   Restart the Home Assistant Docker container to load the updated component.
    *   Navigate to the `Docker` directory: `cd /mnt/e/Source/Repos/homeassistant/Docker`
    *   Restart the container: `docker compose restart homeassistant`
6.  **Verification (HA API):**
    *   After Home Assistant restarts, verify the changes by retrieving the entity data from the Home Assistant API.
    *   Use the Python script `call_ha_api.py` to securely access the API. This script will automatically retrieve the API token from your `secrets.yaml` and make the `curl` request.
    *   Navigate to the `custom_components/price_tracker/custom_components/price_tracker/scripts/` directory.
    *   Execute the script: `python call_ha_api.py`
    *   Inspect the output for the updated entity attributes, especially the `url` attribute, which should now point to the lowest price seller's product page.

### Git Operations for price_tracker Component

All Git operations (branching, adding, committing, pushing) related to the `price_tracker` custom component should be performed from its root directory: `custom_components/price_tracker/`.

*Note: This documentation file is located at `custom_components/price_tracker/.docs/buywisely_service.md` and is part of the `price_tracker` component's Git repository.*

## Best Practices for Agent Interaction

To ensure smooth and accurate interactions, please adhere to the following best practices:

*   **Confirm Access Before Assuming:** Before proceeding with any operation that requires access to files, directories, or external services, explicitly confirm that access is available. Do not assume access based on previous interactions or general knowledge.

*   **Targeted Log Review:** When reviewing logs, focus on the most recent and relevant entries. Avoid reviewing entire log files, as they often contain excessive and irrelevant detail. Use commands or tools that allow you to tail logs or filter by time/keywords.

## Accessing Home Assistant Logs

To diagnose issues and monitor the behavior of the `price_tracker` component, you can access Home Assistant logs in several ways:

1.  **Home Assistant UI:** Navigate to Developer Tools -> Logs within the Home Assistant user interface.
2.  **Docker Container Logs:** If running Home Assistant in a Docker container, you can view the logs using the `docker compose logs` command from your Docker directory:
    ```bash
    docker compose logs homeassistant
    ```
3.  **Log File:** Home Assistant also writes logs to a file within its configuration directory. You can access this file directly:
    ```
    Docker/config/homeassistant.log
    ```
    This file contains detailed log entries that can be helpful for debugging.
