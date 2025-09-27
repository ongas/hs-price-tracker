
import re
import sys

with open('/mnt/e/source/personal_repos/homeassistant/custom_components/price_tracker/new_product_page.html', 'r') as f:
    html = f.read()

matches = re.findall(r'self.__next_f.push\((.*?)\)', html)

for match in matches:
    print(match)
