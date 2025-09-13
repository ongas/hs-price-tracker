import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

_LOGGER = logging.getLogger(__name__)

def fetch_rendered_html(url: str) -> str | None:
    """Fetches the fully rendered HTML content of a given URL using Selenium."""
    _LOGGER.info(f"[SeleniumFetcher] Attempting to fetch rendered HTML for: {url}")
    options = Options()
    options.add_argument("--headless")  # Run Chrome in headless mode
    options.add_argument("--no-sandbox") # Required for some environments
    options.add_argument("--disable-dev-shm-usage") # Overcome limited resource problems
    options.add_argument("--window-size=1920,1080") # Set a consistent window size
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

    driver = None
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)

        # Wait for the __NEXT_DATA__ script to be present
        # This is a heuristic; adjust if the target website's loading changes
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "__NEXT_DATA__"))
        )

        html_content = driver.page_source
        _LOGGER.info(f"[SeleniumFetcher] Successfully fetched rendered HTML for {url}. HTML length: {len(html_content)}")
        return html_content
    except Exception as e:
        _LOGGER.error(f"[SeleniumFetcher] Failed to fetch rendered HTML for {url}: {e}")
        return None
    finally:
        if driver:
            driver.quit()
