"""
BDD step definitions for BuyWisely URL validation (US07).

Covers product URL validation and error handling.
"""

import logging
from behave import given, when, then
from hamcrest import assert_that, is_, not_none

from custom_components.price_tracker.services.buywisely.engine import BuyWiselyEngine
from custom_components.price_tracker.components.error import InvalidItemUrlError

_LOGGER = logging.getLogger(__name__)


# ============================================================================
# US07: Validate Product URLs
# ============================================================================

@given("I have a valid BuyWisely product URL (e.g., a buywisely.com.au product page for a product)")
def step_given_valid_domain(context):
    """Set up valid domain URL."""
    context.product_url = "https://www.buywisely.com.au/product/motorola-moto-g75-5g-256gb-grey-with-buds"
    context.is_valid_url = True


@given("I have an invalid BuyWisely product URL (e.g., an image link, a malformed URL, or a non-product page)")
def step_given_invalid_domain(context):
    """Set up invalid domain URL."""
    context.product_url = "https://www.google.com/product/test-product"
    context.is_valid_url = False


@then("the product is accepted for tracking")
def step_then_accepted(context):
    """Verify acceptance."""
    assert_that(context.result, not_none())
    assert_that(context.error, is_(None))


@then("I receive a clear error message and the product is not tracked")
def step_then_error_not_tracked(context):
    """Verify rejection."""
    assert_that(context.error, not_none())
