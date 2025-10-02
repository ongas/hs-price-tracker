# Price Tracker Dashboard

This directory contains a pre-built dashboard configuration for the Price Tracker integration with clickable product cards.

## Installation

### Option 1: Import Dashboard via UI (Easiest)

1. Open Home Assistant
2. Go to **Settings** → **Dashboards**
3. Click **+ Add Dashboard**
4. Choose **New dashboard from scratch**
5. Name it "Price Tracker"
6. Once created, click the **⋮** menu → **Edit dashboard**
7. Click **⋮** menu again → **Raw configuration editor**
8. Copy the contents of `dashboard.yaml` and paste it
9. Click **Save**

### Option 2: Manual File Installation

1. Copy `dashboard.yaml` to your Home Assistant config directory:
   ```bash
   cp custom_components/price_tracker/lovelace/dashboard.yaml /config/lovelace/price_tracker.yaml
   ```

2. Add to your `configuration.yaml`:
   ```yaml
   lovelace:
     mode: storage
     dashboards:
       price-tracker:
         mode: yaml
         title: Price Tracker
         icon: mdi:cart
         show_in_sidebar: true
         filename: lovelace/price_tracker.yaml
   ```

3. Restart Home Assistant

## Features

The dashboard includes three ways to display products:

### 1. Markdown Card with Clickable Links (Default)
- **No custom components required**
- Shows product name, price, seller, and status
- Click product name to open seller page
- Works out of the box

### 2. Button Cards (Recommended - Requires HACS)
- **Requires:** `button-card` from HACS
- Beautiful product cards with images
- Entire card is clickable
- Best user experience

**To enable:**
1. Install `button-card` from HACS
2. Edit the dashboard
3. Uncomment the button-card section
4. Customize for your tracked products

### 3. Entity Cards (Requires HACS)
- **Requires:** `multiple-entity-row` or `template-entity-row` from HACS
- Clean list view
- Clickable rows

**To enable:**
1. Install `auto-entities` and `multiple-entity-row` from HACS
2. Edit the dashboard
3. Uncomment the entity card options

## Installing Custom Components from HACS

1. Open **HACS** in Home Assistant
2. Go to **Frontend**
3. Click **+ Explore & Download Repositories**
4. Search for:
   - `button-card` (recommended)
   - `multiple-entity-row`
   - `auto-entities`
5. Click **Download**
6. Restart Home Assistant

## Customization

### Change Card Style

Edit the `styles` section in button-card configuration:

```yaml
styles:
  card:
    - height: 100px  # Change card height
    - background-color: var(--card-background-color)
  name:
    - font-size: 16px  # Change name font size
    - color: var(--primary-text-color)
  state:
    - font-size: 24px  # Change price font size
    - color: var(--accent-color)
```

### Filter Products

To show only specific products, modify the markdown card filter:

```yaml
{% for entity in states.sensor | selectattr('entity_id', 'match', 'sensor.price_buywisely_.*motorola.*') | sort(attribute='attributes.name') %}
```

### Sort Products

By price (lowest first):
```yaml
{% for entity in states.sensor | selectattr('entity_id', 'match', 'sensor.price_buywisely_.*') | sort(attribute='state') %}
```

By name:
```yaml
{% for entity in states.sensor | selectattr('entity_id', 'match', 'sensor.price_buywisely_.*') | sort(attribute='attributes.name') %}
```

## Troubleshooting

### Links not clickable
- Ensure you're using the markdown card option (works by default)
- OR install required custom components from HACS

### Products not showing
- Ensure entities start with `sensor.price_buywisely_`
- Check that entities are available (not unavailable/unknown)
- Verify entity IDs match the filter pattern

### Images not showing
- Images are loaded from external sources
- Some sellers may block external image requests
- Product images are stored in the `image` attribute

## Support

For more information, see:
- [Dashboard Configuration Guide](../../../docs/DASHBOARD_CONFIGURATION.md)
- [Price Tracker Documentation](../../../README.md)
