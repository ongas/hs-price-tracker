
import re

file_path = "/mnt/e/source/personal_repos/homeassistant/custom_components/price_tracker/test_buywisely_pushblock_parser.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix line 87: Correct the regex pattern
# Original: cleaned = re.sub(r'^\\\\[1,"11:\\\"\\\\\\\$\\",\\\\\\\$L59\\",null,', '', array_literal)
# Corrected: cleaned = re.sub(r'^\[1,"11:\["\\\$","\\\$L59",null,', '', array_literal)
content = re.sub(
    r"cleaned = re.sub\(r'\^\\\\\\[1,\"11:\\\\\\\[\"\\\\\\\\\\\\\$\\\",\\\\\\\\\\\\\$L59\\\\\",null,\', '', array_literal\)",
    r"cleaned = re.sub(r'^\[1,"11:\["\\\$","\\\$L59",null,', '', array_literal)",
    content
)

# Fix line 127: f-string formatting
content = content.replace(
    r"print(f"Suspicious pattern '{}' found at position {}: ...{}...".format(pat, m.start(), fixed[m.start()-20:m.end()+20]))",
    r"print(f"Suspicious pattern '{pat}' found at position {m.start()}: ...{fixed[m.start()-20:m.end()+20]}...")"
)

# Fix line 134: f-string formatting
content = content.replace(
    r"print("Suspicious pattern '{}' found at position {}: ...{}...".format(pat, len(fixed)-2000+m.start(), fixed[len(fixed)-2000+m.start()-20:len(fixed)-2000+m.end()+20]))",
    r"print(f"Suspicious pattern '{pat}' found at position {len(fixed)-2000+m.start()}: ...{fixed[len(fixed)-2000+m.start()-20:len(fixed)-2000+m.end()+20]}...")"
)

# Fix line 145: f-string formatting
content = content.replace(
    r"print("Suspicious pattern '{}' found at position {}: ...{}...".format(pat, m.start(), fixed[m.start()-20:m.end()+20]))",
    r"print(f"Suspicious pattern '{pat}' found at position {m.start()}: ...{fixed[m.start()-20:m.end()+20]}...")"
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("File updated successfully.")
