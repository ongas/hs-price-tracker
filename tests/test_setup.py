from custom_components.price_tracker.components.setup import PriceTrackerSetup

def test_instantiation():
    setup = PriceTrackerSetup()
    assert isinstance(setup, PriceTrackerSetup)

def test_setup_config_data_none():
    setup = PriceTrackerSetup()
    assert setup.setup_config_data(None) == {}

def test_setup_config_data_with_target():
    setup = PriceTrackerSetup()
    user_input = {"service_type": "buywisely", "target": "foo"}
    result = setup.setup_config_data(user_input)
    assert result["type"] == "buywisely"
    assert result["target"] == "foo"

def test_async_set_unique_id():
    setup = PriceTrackerSetup()
    user_input = {"service_type": "buywisely"}
    assert setup._async_set_unique_id(user_input) == "price-tracker-buywisely"
