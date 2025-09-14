import logging
from custom_components.price_tracker.services.buywisely.parser import parse_product

class LogCapture(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []
    def emit(self, record):
        self.records.append(record)

def test_buywisely_diagnostics_logging():
    logger = logging.getLogger("custom_components.price_tracker.services.buywisely.html_extractor")
    log_capture = LogCapture()
    logger.addHandler(log_capture)
    logger.setLevel(logging.INFO)

    # Invalid JSON triggers fallback and logs error
    html = """
    <html><body>
    <script id=\"__NEXT_DATA__\" type=\"application/json\">{invalid: json}</script>
    <span class='price'>$12.34</span>
    </body></html>
    """
    parse_product(html, product_id="log-1")
    found_fallback = any("BeautifulSoup fallback" in r.getMessage() for r in log_capture.records)
    found_error = any("Failed to parse __NEXT_DATA__ JSON" in r.getMessage() for r in log_capture.records)
    assert found_fallback, "Expected fallback log message not found"
    assert found_error, "Expected JSON parse error log message not found"

    # Remove handler after test
    logger.removeHandler(log_capture)
