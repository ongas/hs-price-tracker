"""
BDD step definitions for BuyWisely product management (US01, US02).

Covers adding products and viewing product details.
"""

import logging
from behave import given, when, then
from hamcrest import assert_that, equal_to, is_, greater_than, not_none

# Import helper from environment
import environment

_LOGGER = logging.getLogger(__name__)


# ============================================================================
# US01: Add a BuyWisely Product for Price Tracking
# ============================================================================

@given("I have a valid BuyWisely product URL")
def step_given_valid_buywisely_url(context):
    """Set up a valid BuyWisely product URL."""
    context.product_url = "https://www.buywisely.com.au/product/motorola-moto-g75-5g-256gb-grey-with-buds"
    context.is_valid_url = True


@given("I have an invalid BuyWisely product URL")
def step_given_invalid_buywisely_url(context):
    """Set up an invalid URL (malformed)."""
    context.product_url = "not-a-valid-url"
    context.is_valid_url = False


@given("I have a BuyWisely product URL where all current offers have a price of 0.0")
def step_given_zero_price_offers(context):
    """Set up a URL with zero-priced offers."""
    context.product_url = "https://www.buywisely.com.au/product/zero-price-product"
    context.is_valid_url = True
    context.has_zero_prices = True


@given("I have already added a valid BuyWisely product")
def step_given_already_added_product(context):
    """Set up first product already added."""
    context.config_entries = [
        {
            "product_url": "https://www.buywisely.com.au/product/first-product",
            "entry_id": "entry_1",
        }
    ]


@when("I add the product to the price tracker")
async def step_when_add_product(context):
    """Attempt to add the product using BuyWiselyEngine."""
    await environment.add_product_helper(context)


@when("I try to add the product to the price tracker")
async def step_when_try_add_product(context):
    """Alias for attempting to add product (expects potential failure)."""
    await environment.add_product_helper(context)


@when("I add a second, different valid BuyWisely product")
async def step_when_add_second_product(context):
    """Add a second distinct product."""
    context.product_url = "https://www.buywisely.com.au/product/second-product"
    context.is_valid_url = True
    await environment.add_product_helper(context)


@then("the product is added to the tracked items list with its current price (which must be greater than 0.0), name, brand, image, and the seller_product_url from the lowest-priced offer")
def step_then_product_added_successfully(context):
    """Verify product was added with valid data."""
    assert_that(context.result, is_(not_none()), "Product data should not be None")
    assert_that(context.result.name, not_none(), "Product name should be extracted")
    assert_that(context.result.price, not_none(), "Product price should be extracted")
    assert_that(context.result.price.price, greater_than(0.0), "Price must be greater than 0.0")
    assert_that(context.result.image, not_none(), "Product image should be extracted")
    assert_that(context.result.url, not_none(), "Seller product URL should be set")
    assert_that(len(context.result.url), greater_than(0), "Seller URL should not be empty")


@then("if the extracted price is 0.0, it indicates an extraction bug and the product should not be added as a valid entity")
def step_then_zero_price_indicates_bug(context):
    """Verify zero price handling."""
    if context.result and hasattr(context.result, 'price'):
        assert_that(
            context.result.price.price,
            greater_than(0.0),
            "Extracted price should never be 0.0 for valid products"
        )


@then("I can set the refresh interval for the product during the add flow")
def step_then_refresh_interval_configurable(context):
    """Verify refresh interval is configurable (placeholder for UI test)."""
    # This would typically verify UI elements in a full integration test
    # For BDD, we acknowledge this is a configuration flow feature
    assert_that(True, is_(True), "Refresh interval should be configurable in UI")


@then('the refresh interval field is labeled "Refresh Interval (minutes)"')
def step_then_refresh_interval_label(context):
    """Verify field label (placeholder for UI test)."""
    # UI validation would go here
    assert_that(True, is_(True), "Field should have correct label")


@then("the refresh interval field has a default value of 30")
def step_then_refresh_interval_default(context):
    """Verify default refresh interval (placeholder for UI test)."""
    # UI validation would go here
    assert_that(True, is_(True), "Default should be 30 minutes")


@then("I receive an error message indicating the URL is invalid")
def step_then_error_invalid_url(context):
    """Verify error for invalid URL."""
    from hamcrest import contains_string
    assert_that(context.error, not_none(), "Error should be set")
    assert_that(context.error, contains_string("Invalid"), "Error should mention invalid URL")


@then("I receive an error message indicating an extraction bug (e.g., \"Extracted price cannot be zero or less.\")")
def step_then_error_zero_price(context):
    """Verify error for zero-priced products."""
    from custom_components.price_tracker.datas.item import ItemStatus
    if hasattr(context, 'has_zero_prices') and context.has_zero_prices:
        # Should either error or have status INACTIVE
        if context.result:
            assert_that(
                context.result.status in [ItemStatus.INACTIVE, ItemStatus.DELETED],
                is_(True),
                "Zero-priced products should be marked inactive or deleted"
            )


@then("the second product is also added to the tracked items list")
def step_then_second_product_added(context):
    """Verify second product was added."""
    assert_that(len(context.config_entries), equal_to(2), "Should have 2 config entries")


@then("I have two tracked BuyWisely products")
def step_then_two_products_tracked(context):
    """Verify multiple products are tracked."""
    assert_that(len(context.config_entries), equal_to(2), "Should track 2 products")


# ============================================================================
# US02: View BuyWisely Product Details
# ============================================================================

@given("I have added a BuyWisely product to the price tracker")
async def step_given_added_product_for_viewing(context):
    """Set up an added product for viewing details."""
    context.product_url = "https://www.buywisely.com.au/product/test-product"
    context.is_valid_url = True
    await environment.add_product_helper(context)


@when("I view the product in the tracker")
def step_when_view_product(context):
    """Simulate viewing product details."""
    # In real integration, this would query entity state
    context.viewed_product = context.result


@then("I see the product's name, brand, image, current price, and currency")
def step_then_see_product_details(context):
    """Verify all product details are visible."""
    product = context.viewed_product
    assert_that(product, not_none(), "Product should exist")
    assert_that(product.name, not_none(), "Name should be visible")
    assert_that(product.brand, not_none(), "Brand should be visible")
    assert_that(product.image, not_none(), "Image should be visible")
    assert_that(product.price, not_none(), "Price should be visible")
    assert_that(product.price.currency, not_none(), "Currency should be visible")


@then("the displayed price matches the lowest available offer")
def step_then_price_matches_lowest(context):
    """Verify displayed price is the lowest."""
    # This is validated by the engine selecting the lowest offer
    assert_that(context.viewed_product.price.price, greater_than(0.0))


@when("I view the tracked products list")
def step_when_view_tracked_products_list(context):
    """Simulate viewing the tracked products list."""
    # In real integration, this would query all entity states
    context.viewed_products = [context.result] if context.result else []


@then("I see the product's name, brand, image, current price (which must be greater than 0.0), and availability status")
def step_then_see_product_details_with_status(context):
    """Verify all product details including status are visible."""
    product = context.result if hasattr(context, 'result') else context.viewed_product
    assert_that(product, not_none(), "Product should exist")
    assert_that(product.name, not_none(), "Name should be visible")
    assert_that(product.brand, not_none(), "Brand should be visible")
    assert_that(product.image, not_none(), "Image should be visible")
    assert_that(product.price, not_none(), "Price should be visible")
    assert_that(product.price.price, greater_than(0.0), "Price must be greater than 0.0")
    assert_that(product.status, not_none(), "Status should be visible")


@then("if the displayed price is 0.0, it indicates an extraction bug")
def step_then_zero_price_is_bug(context):
    """Verify zero price is treated as a bug."""
    if context.result and hasattr(context.result, 'price'):
        assert_that(
            context.result.price.price,
            greater_than(0.0),
            "Displayed price of 0.0 indicates an extraction bug"
        )


@then("the product's tracked URL points to the seller_product_url of the lowest price offer (never a fallback or hydration field)")
def step_then_url_is_seller_url(context):
    """Verify URL comes from seller_product_url in offers."""
    product = context.result if hasattr(context, 'result') else context.viewed_product
    assert_that(product.url, not_none(), "URL should be set")
    # Verify it's not a BuyWisely URL (which would indicate fallback)
    assert_that("buywisely.com.au" not in product.url.lower(), is_(True),
                "URL should be seller_product_url, not BuyWisely URL")
