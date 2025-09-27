
import re

with open('/mnt/e/source/personal_repos/homeassistant/custom_components/price_tracker/next_data.json', 'r') as f:
    for line in f:
        if "product_status":