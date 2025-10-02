# Dashboard Configuration for Clickable Price Tracker Entities

This guide shows how to make price tracker entities clickable on your Home Assistant dashboard, so clicking them opens the seller's product page.

## Option 1: Entity Card with Custom Row (Recommended)

Using the built-in entity card with a custom template:

```yaml
type: entities
entities:
  - entity: sensor.price_buywisely_type_motorola_moto_g75_5g_256gb_grey_with_buds
    type: custom:template-entity-row
    name: "{{ state_attr('sensor.price_buywisely_type_motorola_moto_g75_5g_256gb_grey_with_buds', 'name') }}"
    state: "{{ states('sensor.price_buywisely_type_motorola_moto_g75_5g_256gb_grey_with_buds') }} {{ state_attr('sensor.price_buywisely_type_motorola_moto_g75_5g_256gb_grey_with_buds', 'unit_of_measurement') }}"
    tap_action:
      action: url
      url_path: "{{ state_attr('sensor.price_buywisely_type_motorola_moto_g75_5g_256gb_grey_with_buds', 'url') }}"
```

**Requirements:** Install `template-entity-row` from HACS

## Option 2: Multiple Entity Row (Simple)

Using the `multiple-entity-row` custom component:

```yaml
type: entities
entities:
  - entity: sensor.price_buywisely_type_motorola_moto_g75_5g_256gb_grey_with_buds
    type: custom:multiple-entity-row
    name: Moto G75
    tap_action:
      action: url
      url_path: "[[[ return entity.attributes.url ]]]"
```

**Requirements:** Install `multiple-entity-row` from HACS

## Option 3: Button Card (Most Flexible)

Using the popular `button-card` custom component:

```yaml
type: custom:button-card
entity: sensor.price_buywisely_type_motorola_moto_g75_5g_256gb_grey_with_buds
name: "[[[ return entity.attributes.name ]]]"
show_state: true
show_icon: true
show_entity_picture: true
entity_picture: "[[[ return entity.attributes.image ]]]"
state_display: "[[[ return entity.state + ' ' + entity.attributes.unit_of_measurement ]]]"
tap_action:
  action: url
  url_path: "[[[ return entity.attributes.url ]]]"
styles:
  card:
    - height: 60px
  name:
    - font-size: 14px
  state:
    - font-size: 16px
    - font-weight: bold
```

**Requirements:** Install `button-card` from HACS

## Option 4: Auto-Entities with Card-Mod

Automatically create clickable cards for all price tracker entities:

```yaml
type: custom:auto-entities
card:
  type: entities
  title: Price Tracker
filter:
  include:
    - entity_id: "sensor.price_buywisely_*"
      options:
        type: custom:multiple-entity-row
        tap_action:
          action: url
          url_path: "[[[ return entity.attributes.url ]]]"
```

**Requirements:** Install `auto-entities` and `multiple-entity-row` from HACS

## Option 5: Markdown Card with Links

Simple markdown card with clickable links:

```yaml
type: markdown
content: |
  {% for entity in states.sensor | selectattr('entity_id', 'match', 'sensor.price_buywisely_.*') %}
  [{{ state_attr(entity.entity_id, 'name') }} - {{ states(entity.entity_id) }} {{ state_attr(entity.entity_id, 'unit_of_measurement') }}]({{ state_attr(entity.entity_id, 'url') }})
  {% endfor %}
```

**Requirements:** None (built-in)

## Installing Custom Components

All custom components can be installed via HACS:

1. Open HACS in Home Assistant
2. Go to "Frontend"
3. Click "+ Explore & Download Repositories"
4. Search for the component name
5. Click "Download"
6. Restart Home Assistant

## Recommended Setup

For the best user experience, we recommend **Option 3 (Button Card)** as it provides:
- Clickable entities
- Product images
- Clean layout
- Customizable styling
- Works on mobile and desktop
