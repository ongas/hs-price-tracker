import re
from demjson3 import decode
import pprint

def build_ref_map(content):
    """Builds a reference map from the raw Next.js hydration data."""
    lines = content.splitlines()
    payload_chunks = []
    for line in lines:
        if line.startswith('self.__next_f.push([1,'):
            start = line.find('"')
            end = line.rfind('"')
            if start != -1 and end != -1 and start != end:
                payload_chunks.append(line[start+1:end])

    full_payload = '\n'.join(payload_chunks)
    full_payload = full_payload.replace('\"', '"').replace('\n', '\n')

    records = full_payload.splitlines()
    ref_map = {}
    record_regex = re.compile(r'^([a-zA-Z0-9]+):(.*)')

    for record in records:
        match = record_regex.match(record)
        if match:
            ref_map[match.group(1)] = match.group(2)
    return ref_map

def resolve_recursive(key, ref_map, resolved_cache, level=0):
    """Recursively resolves a reference key with added debugging."""
    indent = "  " * level
    print(f"{indent}Resolving key: {key}")

    if key in resolved_cache:
        print(f"{indent} -> Found in cache.")
        return resolved_cache[key]
    if key not in ref_map:
        print(f"{indent} -> Not in ref_map. Returning as is.")
        return f'"${key}"'

    resolved_cache[key] = '"__RECURSION_GUARD__"'
    value = ref_map[key]
    print(f"{indent} -> Raw value: {value[:100]}...")

    refs = re.findall(r'"\$([a-zA-Z0-9]+)"', value)
    for ref_key in set(refs):
        print(f"{indent}  -> Found ref: ${ref_key}")
        resolved_value = resolve_recursive(ref_key, ref_map, resolved_cache, level + 1)
        value = value.replace(f'"${ref_key}"', resolved_value)
    
    print(f"{indent} -> Resolved value: {value[:100]}...")
    resolved_cache[key] = value
    return value

def run_parser(content):
    ref_map = build_ref_map(content)
    
    if '11' not in ref_map:
        print("Error: Main product record (key '11') not found.")
        return

    print("--- Resolving All References ---")
    resolved_cache = {}
    # We only need to resolve the main key, the recursion will handle the rest.
    final_string = resolve_recursive('11', ref_map, resolved_cache)

    # Final cleanup
    final_string = re.sub(r'"\$D(.*?)"', r'"\1"', final_string)
    final_string = re.sub(r'T[a-zA-Z0-9]+,', '', final_string)
    final_string = final_string.replace('"$Sreact.fragment"' , '"react.fragment"')
    final_string = final_string.replace('"$",', '')

    # Extract the product dictionary
    dict_match = re.search(r'({\s*"product":\s*{.*}})', final_string, re.DOTALL)
    if not dict_match:
        print("Could not extract the product dictionary.")
        print("\n--- Final String (for debugging) ---")
        print(final_string)
        return

    final_json_string = dict_match.group(1)

    print("--- Final Parsed Product Data ---")
    try:
        final_data = decode(final_json_string)
        pprint.pprint(final_data)
    except Exception as e:
        print(f"Failed to parse final JSON string: {e}")
        print("\n--- Final JSON String (for debugging) ---")
        print(final_json_string)

if __name__ == "__main__":
    try:
        with open('tests/buywisely/fixtures/nextjs_json_string.txt', 'r') as f:
            content = f.read()
        run_parser(content)
    except FileNotFoundError:
        print("Error: problematic_json_string.txt not found.")
    except Exception as e:
        print(f"An error occurred: {e}")