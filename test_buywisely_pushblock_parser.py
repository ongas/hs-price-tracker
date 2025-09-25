# Test utility for BuyWisely hydration parser using real push block

import re
import demjson3
import tolerantjson
import pytest
import codecs

from custom_components.price_tracker.services.buywisely.json_parser_utils import unescape_json_string, extract_js_literal_from_push_string, remove_js_prefix

def robust_stateful_cleaner(data_string: str) -> str:
    """
    A state-aware parser to robustly clean the JSON-like data from BuyWisely.
    This approach is more resilient to changes in string content than regex replacements.
    """
    in_string = False
    is_escaped = False
    result = []
    
    i = 0
    while i < len(data_string):
        char = data_string[i]
        
        if in_string:
            if is_escaped:
                # The previous character was a backslash, so append this character literally
                result.append(char)
                is_escaped = False
            elif char == '\\':
                # This is an escape character, note it for the next iteration
                is_escaped = True
                result.append(char)
            elif char == '"':
                # We are leaving a string
                in_string = False
                result.append(char)
            else:
                # A regular character inside a string
                result.append(char)
        else:  # We are not in a string
            if char == '"':
                # We are entering a string
                in_string = True
                result.append(char)
            # Handle custom formats only when not in a string
            elif char == '$' and data_string[i:i+2] == '$D':
                # Match and wrap custom date objects like "$D2024-..." in quotes
                date_match = re.match(r'(\$D[\dTZ:.-]+)', data_string[i:])
                if date_match:
                    date_str = date_match.group(1)
                    result.append(f'"{date_str}"')
                    i += len(date_str) - 1  # Skip ahead
                else:
                    result.append(char)
            elif char == '<' and data_string[i:i+4] == '<$':
                # Match and replace React fragments like "<$L_..." with null
                fragment_match = re.match(r'(<\$L_[\w./]+>)', data_string[i:])
                if fragment_match:
                    fragment_str = fragment_match.group(1)
                    result.append('null')
                    i += len(fragment_str) - 1  # Skip ahead
                else:
                    result.append(char)
            else:
                # A regular character outside a string
                result.append(char)
        i += 1
        
    return "".join(result)

# Load the real push block string
with open('buywisely_pushblock_full_runtime.txt', 'r', encoding='utf-8') as f:
    content = f.read()
    # Look for self.__next_f.push([...])
    m = re.search(r'self\.__next_f\.push\((.*)\)', content, re.DOTALL)
    if not m:
        raise ValueError('No self.__next_f.push([ ... ]) block found in file!')
    push_block = m.group(1)


# Extract the inner JS literal string (the second argument)
js_literal = extract_js_literal_from_push_string(push_block)


# Remove leading XX: prefix (e.g., 11:)
js_literal_no_prefix = remove_js_prefix(js_literal)

# If the string is quoted, strip the outer quotes
if js_literal_no_prefix.startswith('"') and js_literal_no_prefix.endswith('"'):
    js_literal_no_prefix = js_literal_no_prefix[1:-1]

# Unescape and clean the string
unescaped = unescape_json_string(js_literal_no_prefix)

# Decode unicode escape sequences (e.g., \u0026 -> &)
decoded = unescaped.encode('utf-8').decode('unicode_escape')

print('Intermediate cleaned string:', decoded[:500])

# Try to extract the array literal from the cleaned string
array_match = re.search(r'(\[.*\])', decoded, re.DOTALL)
if array_match:
    array_literal = array_match.group(1)
else:
    array_literal = decoded

# Use the new robust cleaner
fixed = robust_stateful_cleaner(array_literal)

print('--- After Robust Cleaning ---')
print(fixed[:2000])

try:
    parsed = demjson3.decode(fixed)
    print('\n--- Successfully parsed with demjson3! ---')
    print('Parsed object:', parsed)

except demjson3.JSONDecodeError as e:
    print(f'\n--- demjson3 parse error: {e} ---')
    pos = getattr(e, 'pos', None)
    if pos is not None:
        print(f'Error at position {pos}')
        print('200 chars before error:', fixed[max(0, pos-200):pos])
        print('200 chars after error:', fixed[pos:pos+200])
    
    # Fallback to tolerantjson
    print('\n--- Falling back to tolerantjson ---')
    try:
        parsed = tolerantjson.tolerate(fixed)
        print('Successfully parsed with tolerantjson!')
        print('Parsed object:', parsed)
    except Exception as tj_err:
        print(f'tolerantjson parse error: {tj_err}')
        pytest.fail("Both demjson3 and tolerantjson failed to parse the data.")

# You can add further checks on the 'parsed' object here
