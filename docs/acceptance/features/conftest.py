"""
Shared fixtures for Behave BDD tests.

This module provides reusable test fixtures, mocks, and helpers
for testing the BuyWisely integration with Home Assistant.
"""

import sys
from pathlib import Path

# Ensure the project root is in the Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import test fixtures from pytest tests
FIXTURES_DIR = project_root / "tests" / "buywisely" / "fixtures"


def load_html_fixture(filename: str) -> str:
    """
    Load an HTML fixture file.

    Args:
        filename: Name of the fixture file

    Returns:
        str: Contents of the fixture file
    """
    fixture_path = FIXTURES_DIR / filename
    if not fixture_path.exists():
        raise FileNotFoundError(f"Fixture not found: {fixture_path}")

    with open(fixture_path, encoding="utf-8") as f:
        return f.read()


def load_test_data(filename: str) -> str:
    """
    Load test data JSON from docs/acceptance/test_data/buywisely/.

    Args:
        filename: Name of the test data file

    Returns:
        str: Contents of the test data file
    """
    test_data_dir = project_root / "docs" / "acceptance" / "test_data" / "buywisely"
    test_data_path = test_data_dir / filename

    if not test_data_path.exists():
        raise FileNotFoundError(f"Test data not found: {test_data_path}")

    with open(test_data_path, encoding="utf-8") as f:
        return f.read()


# Common test URLs
VALID_BUYWISELY_URL = "https://www.buywisely.com.au/product/motorola-moto-g75-5g-256gb-grey-with-buds"
INVALID_URL = "not-a-valid-url"
INVALID_DOMAIN_URL = "https://www.google.com/product/some-product"
INVALID_NO_PRODUCT_URL = "https://www.buywisely.com.au/category/some-category"
