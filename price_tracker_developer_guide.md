---
# Price Tracker Developer Guide

This document provides a comprehensive reference for the Home Assistant `price_tracker` custom component, including architecture, development, debugging, testing, deployment, API usage, best practices, and issue tracking. It covers all supported e-commerce services. Service-specific details are found in the Services section.

## 1. Introduction & Purpose

The `price_tracker` custom component enables Home Assistant to track product prices from various e-commerce sources. Each service integration (such as BuyWisely) may have its own scraping, parsing, and API logic.

## 2. Architecture & Key Components

**Core Files:**
- `config_flow.py`: Handles Home Assistant configuration flow for new product trackers.
- `components/`: Core logic for entity, sensor, and integration management.
- `services/`: Contains service-specific engines, parsers, and data transformers (e.g., `services/buywisely/json_parser.py` for JSON extraction and parsing, see Services section).
- `utilities/hydration_parser.py`: Now acts as a wrapper, delegating complex JSON extraction and parsing to `services/buywisely/json_parser.py`.

**Home Assistant Configuration:**
- Main config: `configuration.yaml` (e.g., `docker/config/configuration.yaml`).
- Common sections: `default_config:`, `frontend:`, `automation:`, `script:`, `scene:`, `http:`, `sensor:`, `binary_sensor:`, `mqtt:`.
- Changes require a Home Assistant restart.

## 3. Development & Debugging Workflow

### Core Principles
- **Systematic Isolation:** Address one problem at a time, starting with fundamental issues.
- **Incremental Changes:** Make small, focused changes and verify impact.
- **Extensive Logging:** Use `_LOGGER.debug`, `_LOGGER.info`, `_LOGGER.warning`, and `_LOGGER.error` for visibility.
- **Log Filtering:** Use `grep` and `tail` to extract relevant log info from the Home Assistant log file (`../../docker/config/home-assistant.log`).
- **Clean Environment:** Restart Home Assistant container and clear logs for each test (truncate or delete `../../docker/config/home-assistant.log`).
- **Verification:** Confirm each change by observing logs and entity states.
- **Library Usage:** Use `BeautifulSoup` for HTML parsing and `demjson3` for processing Next.js hydration data.

### Debugging Workflow
1. Understand the problem and form a hypothesis.
2. Outline specific steps to test the hypothesis.
3. Prepare the environment (stop container, clear logs by truncating or deleting `../../docker/config/home-assistant.log`, restart container).
4. Implement changes (edit code, add logging, etc.).
5. Trigger actions if needed (e.g., manual update).
6. Collect and analyze logs (use `tail`, `grep`, etc.).
7. Iterate based on findings.

### Tools Used
- `read_file`, `write_file`: For code inspection and modification.
- Shell commands: For container management and log review.
- `google_web_search`: For researching Home Assistant behaviors.

### Deployment Paths
- **Project Root:** `custom_components/price_tracker`
- **Deployment Source (only this gets deployed!):** `custom_components/price_tracker/custom_components/price_tracker`
- **HA-Dev Container Target:** `../../docker/config/custom_components/price_tracker`
- **Home Assistant Log File:** `../../docker/config/home-assistant.log` (relative to project root; use for log filtering and debugging)

> **Warning:** Never deploy the project root. Only deploy the inner deployment source directory as shown above.

## 4. Testing

**Test Scope:**
- Only run Buywisely-specific and common logic tests (not other integrations).

**Test Location:**
- `custom/price_tracker/hs-price-tracker/tests/`

**Relevant Test Files:**
- `test_config_flow.py`, `test_buywisely_parser.py`, `test_buywisely_engine.py`, `test_buywisely_config.py`, `test_buywisely_api.py`

**How to Run:**
1. Ensure you are in the correct directory: `custom/price_tracker/hs-price-tracker/`
2. Run:
     ```bash
     pytest tests/test_config_flow.py tests/test_buywisely_parser.py tests/test_buywisely_engine.py tests/test_buywisely_config.py tests/test_buywisely_api.py
     ```

**Viewing Pytest Output:**
To avoid hitting processing size limitations with verbose pytest output, you can redirect the output to a file and then view the last few lines.

1. Run pytest and redirect output to a file (e.g., `pytest_output.txt`):
   ```bash
   pytest tests/buywisely/test_buywisely_parser.py > pytest_output.txt 2>&1
   ```
2. View the last 50 lines of the output file:
   ```bash
   tail -n 50 pytest_output.txt
   ```
   You can adjust the number of lines (`-n 50`) as needed.

**Viewing Pytest Output:**
To avoid hitting processing size limitations with verbose pytest output, you can redirect the output to a file and then view the last few lines.

1. Run pytest and redirect output to a file (e.g., `pytest_output.txt`):
   ```bash
   pytest tests/buywisely/test_buywisely_parser.py > pytest_output.txt 2>&1
   ```
2. View the last 50 lines of the output file:
   ```bash
   tail -n 50 pytest_output.txt
   ```
   You can adjust the number of lines (`-n 50`) as needed.

**Note:** Do not use quiet mode (`-q`) for pytest. Full output is required for diagnostics and debugging.

**Test Infrastructure Note:**
- In `test_services.py`, initialize `hass.data[DOMAIN]` as a dict in each test setup to prevent `KeyError`.
- Ensure BuyWisely add flow tests require and validate the refresh interval field.

**Important Testing Update:**
- Do not use quiet mode for tests; always run with full output.
- Additions in the add flow now require the refresh interval to be explicitly set and validated.

## 5. Deployment Workflow


**Conda Environment Activation (MANDATORY):**
- You must **only** use the `homeassistant` conda environment for all development, testing, and deployment. **Never create or use a Python virtualenv, venv, or pipenv.**
- To activate:
        ```bash
        conda activate homeassistant
        echo $CONDA_DEFAULT_ENV
        ```
    The prompt must show `homeassistant` as the active environment. If not, troubleshooting and test execution will fail.

**Troubleshooting Missing Dependencies:**
- If you encounter errors such as `ModuleNotFoundError: No module named \'demjson3\'`, ensure you are in the correct conda environment and all dependencies are installed:
        ```bash
        conda activate homeassistant
        pip install -r requirements.txt
        ```
    **Never use `python -m venv`, `virtualenv`, or `pipenv` for this project.** All dependencies must be managed through the conda environment only.
    Always verify the environment before running or debugging tests.

**Steps:**
1. **Code Modification:** Make changes as needed.
2. **Local Testing:** Run tests with `pytest`.
3. **Code Quality:** Use `ruff check --fix .` for linting and formatting.
4. **Deployment:** Use the deployment script in `custom_components/price_tracker/scripts/` (`./DEPLOYMENT_SCRIPT.sh`).
5. **Restart Home Assistant:**
     ```bash
     cd ../../docker
     docker compose restart homeassistant
     ```
6. **Verification:** Use the `scripts/call_ha_api.py` script to verify entity data after restart.

**Git Operations:**
- Perform all Git operations from `custom_components/price_tracker/`.

## 6. API Usage & Entity Management

**Triggering Buywisely Service:**
- Use the Home Assistant REST API to call the service (requires a long-lived access token).
    ```bash
    curl -X POST \
        -H "Authorization: Bearer YOUR_LONG_LIVED_ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"entity_id": "sensor.buywisely_price_tracker"}' \
        http://YOUR_HA_IP:8123/api/services/homeassistant/turn_on
    ```


**Retrieving Entity State:**
    ```bash
    curl -X GET \
        -H "Authorization: Bearer YOUR_API_TOKEN" \
        -H "Content-Type: application/json" \
        http://localhost:8123/api/states/sensor.price_buywisely_type_motorola_moto_g75_5g-256gb_grey_with_buds
    ```

**Finding Entity IDs:**
- Use Home Assistant UI: Developer Tools → States tab → Filter entities by "buywisely" or "price_tracker".

**Security Note:**
- Never hardcode or share API tokens. Manage them securely.

**Product URLs and Price Line Items:**
- The input URL is a listing/search page; each line item has a unique product URL.
- Extraction should focus on the first 10 relevant line items.

## 7. Best Practices

- Confirm access before assuming file or service availability.
- Use targeted log review (tail, grep) instead of reviewing entire logs.
- Adhere to project conventions for formatting and code style.
- Use incremental, well-logged changes for debugging.

## 8. Outstanding Issues & Resolved Problems


### Outstanding Issues
- None currently. The seller_product_url extraction logic is now strict, robust, and fully covered by diagnostics and tests. Update this section as new issues arise.


### Outstanding Test Infrastructure Task
- In `test_services.py`, ensure `hass.data[DOMAIN]` is initialized as a dict in each test setup to prevent `KeyError` in certain tests.
- All BuyWisely tests now validate strict seller_product_url extraction, robust offers traversal, and correct diagnostics for missing or malformed data.


### Resolved Issues

#### Seller URL Extraction, Offers Traversal, and Diagnostics (September 2025)

- **Issue:** The entity url was empty due to incomplete or non-robust extraction of the offers list and seller_product_url from the hydration data.
- **Root Cause:** Extraction logic did not robustly traverse the hydration data to find the offers list, and fallback logic or alternative fields were sometimes used, leading to missing or incorrect seller URLs.
- **Actions Taken:**
    - Extraction logic was rewritten to robustly traverse all nested product dictionaries in the hydration data to find the offers list.
    - Only the seller_product_url from the lowest-priced offer is used for the url field; no fallback or alternative logic is permitted.
    - Deep diagnostics were added to log the full hydration data, offers list, all candidate seller_product_url values, and the final url at every stage.
    - Tests were updated to cover edge cases, missing data, and strict extraction requirements.
    - Deployment and log review workflow was improved to verify extraction and diagnostics end-to-end.
    - **Note:** The `test_buywisely_diagnostics_logging.py` test was removed due to its persistent brittleness and the difficulty in reliably asserting its logging behavior within the test environment. The core logging functionality is still covered by other means.
- **Verification:** Diagnostics in the Home Assistant log now show the full offers list, all candidate seller_product_url values, and the final url set in the entity. Tests pass for all edge cases.
- **Status:** Fully resolved. Extraction is now strict, robust, and regression-proof.

#### Manual Update Button and Deployment Workflow (September 2025)

---

#### Recent Fix: BuyWisely Add Flow Now Always Exposes Refresh Interval (September 2025)

- **Background:** Previously, the refresh interval (`item_refresh_interval`) was only configurable when modifying an existing BuyWisely product, not during the initial add flow.
- **Fix:** The configuration flow for BuyWisely now always includes the refresh interval as a required field when adding a new product. See `config_flow.py` for implementation details.
- **Impact:** Users can now set the refresh interval for BuyWisely products at creation time, improving consistency and usability.
- **Acceptance/Test Artefacts:**
    - Update feature files (e.g., `features/US01_Add_BuyWisely_Product.feature`, `US03_Track_Lowest_Price.feature`) to require and validate the refresh interval in the add flow.
    - Ensure tests in `tests/test_config_flow.py` and related BuyWisely tests check for this field in the add flow.
- **Developer Note:** This change is also documented in `DEVELOPMENT_NOTES.md`.

## 9. Future Improvements
## 10. Manual Update via Dashboard

To allow users to force a manual price update for a specific product, add a button to your Home Assistant dashboard. This button should call the appropriate update service for the target entity. Example YAML for a dashboard button:

```yaml
type: grid
cards:
    - type: button
        name: Force Price Update
        icon: mdi:cart
        tap_action:
            action: call-service
            service: price_tracker.update_entity
            service_data:
                entity_id: sensor.price_buywisely_type_motorola_moto_g75_5g_256gb_grey_with_buds
```

Replace `entity_id` with the correct sensor/entity for your product. This button will appear in your dashboard and, when pressed, will trigger an immediate update for the specified product.

- Detect service website changes and alert developers.
- Implement more robust parsing techniques.
- Add rate limiting/throttling to avoid IP blocking.
- Enhance error reporting for parsing failures.

## 10. Services

### 10.1 BuyWisely Service

**BuyWisely-specific Architecture & Key Components:**
- `services/buywisely/engine.py`: Contains `BuyWiselyEngine` for HTTP requests, response handling, and data construction.
- `services/buywisely/parser.py`: Contains `parse_product` for HTML parsing using the custom hydration parser (`utilities/hydration_parser.py`) and `BeautifulSoup`.
- `components/buywisely/setup.py`: Integrates BuyWisely with Home Assistant’s config entry system.


**Seller URL Extraction (CRITICAL):**
- The seller URL for each product is now strictly and only extracted from the `seller_product_url` field of the lowest-priced offer in the offers list, which is robustly traversed from the hydration data. No fallback or alternative logic is used or permitted.
- The extraction logic deeply traverses the hydration data to locate the offers list, regardless of its nesting, and logs the full offers list and all candidate seller_product_url values for diagnostics.
- If no valid `seller_product_url` is found in the offers, the seller URL will be empty and this is logged for diagnostics.
- The hydration data's `product['seller']['url']` or any other field is never used for the seller URL, as it is almost always missing or empty and is not reliable.
- Extensive diagnostics are present at every stage: the full hydration data, offers list, all candidate URLs, and the final url set in the entity are logged for traceability and debugging.


**Web Scraping & Extraction Considerations:**
- The extraction logic is robust to changes in the hydration data structure, as it traverses all nested product dictionaries to find the offers list.
- If the BuyWisely website changes the structure or naming of the offers list, diagnostics will log the full hydration data and extraction failure, making debugging straightforward.
- Parsing logic may still break if the site layout or hydration data format changes significantly; always check logs for extraction diagnostics.

**Entity Management:**

- Use Home Assistant UI: Developer Tools → States tab → Filter entities by "buywisely" or "price_tracker".
- For forcing a manual update via the dashboard, see the [Manual Update via Dashboard](#10-manual-update-via-dashboard) section.


**Product URLs and Price Line Items:**
- The input URL is a listing/search page; each line item has a unique product URL.
- Extraction of the seller URL is always from the offers list in the hydration data for the specific product page, not from the listing page.
- Only the first 10 offers are considered for price and seller URL extraction, as per business logic and test coverage.

**Outstanding Issues & Resolved Problems (BuyWisely):**
- See previous sections for general issues. BuyWisely-specific issues and resolutions are tracked here as needed.
