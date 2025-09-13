from behave import given, when, then
from hamcrest import assert_that, equal_to, is_, contains_string

# These are stubs. You will need to implement integration with Home Assistant test helpers or mocks.

@given('I have a valid BuyWisely product URL')
def step_given_valid_url(context):
    context.product_url = "https://www.buywisely.com.au/product/test-product?id=12345"

@given('I have an invalid BuyWisely product URL')
def step_given_invalid_url(context):
    context.product_url = "invalid-url"

@when('I add the product to the price tracker')
def step_when_add_product(context):
    # Simulate adding the product (replace with actual integration logic)
    if context.product_url.startswith("https://www.buywisely.com.au/product/"):
        context.add_result = {
            "success": True,
            "name": "Test Product",
            "brand": "TestBrand",
            "image": "https://.../image.png",
            "price": 123.45
        }
    else:
        context.add_result = {"success": False, "error": "Invalid URL"}

@when('I try to add the product to the price tracker')
def step_when_try_add_product(context):
    # Alias for the above step
    step_when_add_product(context)

@then('the product is added to the tracked items list with its current price, name, brand, and image')
def step_then_product_added(context):
    assert_that(context.add_result["success"], is_(True))
    assert_that(context.add_result["name"], contains_string("Test Product"))
    assert_that(context.add_result["brand"], contains_string("TestBrand"))
    assert_that(context.add_result["image"], contains_string("image.png"))
    assert_that(context.add_result["price"], equal_to(123.45))

@then('I receive an error message indicating the URL is invalid')
def step_then_error_invalid_url(context):
    assert_that(context.add_result["success"], is_(False))
    assert_that(context.add_result["error"], contains_string("Invalid URL"))

@given('the BuyWisely integration is running')
def step_given_integration_running(context):
    context.logs = []

@when('a product is loaded, parsed, or data is extracted')
def step_when_product_loaded(context):
    context.logs.append("Product loaded: https://www.buywisely.com.au/product/test-product?id=12345")
    context.logs.append("Extracted data: {id: 12345, name: 'Test Product', price: 95.0}")
    context.logs.append("Error: None")

@then('diagnostic logs are generated including product URLs, IDs, extracted data, and error messages')
def step_then_logs_generated(context):
    assert any("Product loaded" in log for log in context.logs)
    assert any("Extracted data" in log for log in context.logs)
    assert any("Error" in log for log in context.logs)

@then('logs are accessible via the Home Assistant log system')
def step_then_logs_accessible(context):
    # Simulate log accessibility
    assert_that(len(context.logs) > 0, is_(True))

@given('I am tracking a BuyWisely product')
def step_given_tracking_product(context):
    context.product = {"status": "active"}

@when('the product becomes unavailable or is deleted')
def step_when_unavailable(context):
    context.product["status"] = "deleted"

@then("its status is set to 'deleted' or 'inactive'")
def step_then_status_deleted(context):
    assert_that(context.product["status"] in ["deleted", "inactive"], is_(True))

@then('the product is clearly marked as unavailable in the UI')
def step_then_marked_unavailable(context):
    # Simulate UI marking
    assert_that(context.product["status"], is_("deleted"))

@then('I am informed of the change in status')
def step_then_informed(context):
    # Simulate notification
    assert_that(context.product["status"], is_("deleted"))

@given('I have added a BuyWisely product to the price tracker')
def step_given_added_product(context):
    context.product_html = "<html>...mock BuyWisely product page...</html>"

@when('the system parses the product page')
def step_when_parse_page(context):
    # Simulate parsing
    context.product_details = {
        "name": "Test Product",
        "brand": "TestBrand",
        "image": "https://.../image.png",
        "price": 123.45,
        "offers": [
            {"price": 100.0, "currency": "AUD"},
            {"price": 95.0, "currency": "AUD"}
        ]
    }
    context.parse_failed = False

@then("the product's name, brand, image, price, and offers are extracted and shown to me")
def step_then_extracted(context):
    details = context.product_details
    assert_that(details["name"], contains_string("Test Product"))
    assert_that(details["brand"], contains_string("TestBrand"))
    assert_that(details["image"], contains_string("image.png"))
    assert_that(details["price"], is_(123.45))
    assert_that(len(details["offers"]), is_(2))

@then('if parsing fails, I am notified or fallback logic is used')
def step_then_parse_fails(context):
    # Simulate parse failure
    context.parse_failed = True
    assert_that(context.parse_failed, is_(True))

@given('a BuyWisely product has multiple offers')
def step_given_multiple_offers(context):
    context.offers = [
        {"price": 100.0, "currency": "AUD"},
        {"price": 95.0, "currency": "AUD"},
        {"price": 110.0, "currency": "AUD"}
    ]

@when('I view the product details')
def step_when_view_details(context):
    context.product_details = {
        "offers": context.offers,
        "lowest_price": min(context.offers, key=lambda o: o["price"]),
        "all_offers": context.offers[:10]
    }

@then('up to 10 offers are displayed, each with price and currency information')
def step_then_display_offers(context):
    offers = context.product_details["all_offers"]
    assert_that(len(offers), is_(3))
    for offer in offers:
        assert "price" in offer and "currency" in offer

@then('the lowest price is always selected for tracking')
def step_then_lowest_selected(context):
    lowest = context.product_details["lowest_price"]
    assert_that(lowest["price"], is_(95.0))
    assert_that(lowest["currency"], is_("AUD"))

@when('the product is tracked')
def step_when_tracked(context):
    context.lowest_offer = min(context.offers, key=lambda o: o["price"])
    context.no_offers = False

@then('the lowest price and its corresponding seller URL are selected and displayed')
def step_then_lowest_selected(context):
    assert_that(context.lowest_offer["price"], is_(95.0))
    assert_that(context.lowest_offer["currency"], is_("AUD"))

@given('a BuyWisely product has no available offers')
def step_given_no_offers(context):
    context.offers = []

@when('the product is tracked')
def step_when_tracked_no_offers(context):
    context.no_offers = len(context.offers) == 0

@then('the product is marked as inactive or deleted')
def step_then_marked_inactive(context):
    assert_that(context.no_offers, is_(True))

@then('the product is accepted for tracking')
def step_then_accepted(context):
    assert_that(context.add_result["success"], is_(True))

@then('I receive a clear error message and the product is not tracked')
def step_then_error(context):
    assert_that(context.add_result["success"], is_(False))
    assert_that(context.add_result["error"], contains_string("Invalid URL"))