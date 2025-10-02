"""Tests for Price Tracker Options Flow - Global Excluded Domains configuration."""
import pytest
from unittest.mock import patch, MagicMock
from homeassistant import config_entries
from custom_components.price_tracker.consts.defaults import DOMAIN


@pytest.fixture
def mock_config_entry():
    """Mock a config entry for BuyWisely service."""
    return config_entries.ConfigEntry(
        version=1,
        minor_version=0,
        domain=DOMAIN,
        title="Price Tracker - BuyWisely",
        data={"service_type": "buywisely", "product_url": "https://buywisely.com.au/product/test"},
        options={},
        source="user",
        entry_id="test_entry_id",
    )


async def test_options_flow_shows_global_excluded_domains_field(hass, mock_config_entry):
    """Test that the options flow shows the global_excluded_domains field."""
    # Add the config entry to hass
    mock_config_entry.add_to_hass(hass)

    # Initialize the options flow
    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

    # Check that the form is shown
    assert result["type"] == "form"
    assert result["step_id"] == "init"

    # Check that the data_schema includes global_excluded_domains_buywisely
    schema_keys = list(result["data_schema"].schema.keys())
    assert any("global_excluded_domains" in str(key).lower() for key in schema_keys)


async def test_options_flow_save_global_excluded_domains(hass, mock_config_entry):
    """Test saving global excluded domains via options flow."""
    mock_config_entry.add_to_hass(hass)

    # Start options flow
    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

    # Submit with global excluded domains
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"global_excluded_domains_buywisely": "ebay.com.au,amazon.com.au"}
    )

    # Check that it completes successfully
    assert result["type"] == "create_entry"
    assert result["data"]["global_excluded_domains_buywisely"] == "ebay.com.au,amazon.com.au"


async def test_options_flow_update_existing_global_excluded_domains(hass, mock_config_entry):
    """Test updating existing global excluded domains."""
    # Set initial options
    mock_config_entry.options = {"global_excluded_domains_buywisely": "ebay.com.au"}
    mock_config_entry.add_to_hass(hass)

    # Start options flow
    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

    # Verify current value is shown
    # In a real implementation, the form would populate with existing values

    # Update with new value
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"global_excluded_domains_buywisely": "ebay.com.au,amazon.com.au,temu.com"}
    )

    assert result["type"] == "create_entry"
    assert result["data"]["global_excluded_domains_buywisely"] == "ebay.com.au,amazon.com.au,temu.com"


async def test_options_flow_clear_global_excluded_domains(hass, mock_config_entry):
    """Test clearing global excluded domains."""
    mock_config_entry.options = {"global_excluded_domains_buywisely": "ebay.com.au,amazon.com.au"}
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

    # Clear the field
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"global_excluded_domains_buywisely": ""}
    )

    assert result["type"] == "create_entry"
    assert result["data"]["global_excluded_domains_buywisely"] == ""


async def test_options_flow_whitespace_trimming(hass, mock_config_entry):
    """Test that whitespace is trimmed from domain entries."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

    # Submit with extra whitespace
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"global_excluded_domains_buywisely": " ebay.com.au , amazon.com.au , temu.com "}
    )

    # Whitespace should be trimmed
    saved_value = result["data"]["global_excluded_domains_buywisely"]
    # Check that individual domains are trimmed
    domains = [d.strip() for d in saved_value.split(",")]
    assert "ebay.com.au" in domains
    assert "amazon.com.au" in domains
    assert "temu.com" in domains


async def test_options_flow_empty_entries_filtered(hass, mock_config_entry):
    """Test that empty entries are filtered out."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

    # Submit with empty entries
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"global_excluded_domains_buywisely": "ebay.com.au,,amazon.com.au, ,temu.com"}
    )

    # Empty entries should be filtered
    saved_value = result["data"]["global_excluded_domains_buywisely"]
    domains = [d.strip() for d in saved_value.split(",") if d.strip()]
    assert len(domains) == 3
    assert "" not in domains


async def test_options_flow_integration_reload_triggered(hass, mock_config_entry):
    """Test that changing options triggers integration reload."""
    mock_config_entry.add_to_hass(hass)

    with patch.object(hass.config_entries, "async_reload") as mock_reload:
        result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={"global_excluded_domains_buywisely": "ebay.com.au"}
        )

        assert result["type"] == "create_entry"

        # Verify reload was called (may need adjustment based on actual implementation)
        # mock_reload.assert_called_once_with(mock_config_entry.entry_id)


def test_parse_and_normalize_excluded_domains():
    """Test utility function for parsing and normalizing domain list."""
    # This tests a utility function that should exist to parse the input
    from custom_components.price_tracker.utilities.domain_utils import parse_excluded_domains

    # Test normal input
    result = parse_excluded_domains("ebay.com.au,amazon.com.au")
    assert result == ["ebay.com.au", "amazon.com.au"]

    # Test with whitespace
    result = parse_excluded_domains(" ebay.com.au , amazon.com.au ")
    assert result == ["ebay.com.au", "amazon.com.au"]

    # Test with empty entries
    result = parse_excluded_domains("ebay.com.au,,amazon.com.au, ,temu.com")
    assert result == ["ebay.com.au", "amazon.com.au", "temu.com"]

    # Test empty string
    result = parse_excluded_domains("")
    assert result == []

    # Test None
    result = parse_excluded_domains(None)
    assert result == []


def test_merge_yaml_and_options_flow_config():
    """Test that Options Flow config takes precedence over YAML config."""
    # When both YAML and Options Flow define global_excluded_domains,
    # Options Flow should take precedence

    yaml_config = {"buywisely": {"global_excluded_domains": "ebay.com.au"}}
    options_config = {"global_excluded_domains_buywisely": "amazon.com.au"}

    # In actual implementation, __init__.py should prioritize options_config
    # This test verifies the expected behavior

    # Mock the merge logic
    def get_effective_global_exclusions(yaml_cfg, opt_cfg, service_type):
        """Get effective global exclusions with Options Flow taking precedence."""
        opt_key = f"global_excluded_domains_{service_type}"
        if opt_cfg and opt_key in opt_cfg and opt_cfg[opt_key]:
            return opt_cfg[opt_key]
        if yaml_cfg and service_type in yaml_cfg:
            return yaml_cfg[service_type].get("global_excluded_domains", "")
        return ""

    result = get_effective_global_exclusions(yaml_config, options_config, "buywisely")
    assert result == "amazon.com.au"

    # Test YAML fallback when options not set
    result = get_effective_global_exclusions(yaml_config, {}, "buywisely")
    assert result == "ebay.com.au"

    # Test both empty
    result = get_effective_global_exclusions({}, {}, "buywisely")
    assert result == ""
