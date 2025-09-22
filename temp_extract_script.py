import re

file_path = 'tests/buywisely/fixtures/nextjs_json_string.txt'
with open(file_path, 'r', encoding='utf-8') as f:
    html_content = f.read()

# Regex to find __NEXT_DATA__ = {...};
# This regex is from the hydration_parser.py file
match = re.search(r'__NEXT_DATA__ = (.*?);', html_content, re.DOTALL)

if match:
    extracted_string = match.group(1)
    print(extracted_string[:500]) # Print first 500 characters to avoid flooding output
    print("Length of extracted string: " + str(len(extracted_string)))
else:
    print("No match found for __NEXT_DATA__")
