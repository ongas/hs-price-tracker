# Diagnostic dump of the extracted array literal for offline inspection
with open('buywisely_pushblock_extracted_array_literal.txt', 'w', encoding='utf-8') as f:
    f.write('''
# Extracted array literal (first 2000 chars):\n''')
    f.write(array_literal[:2000])
    f.write('\n\n# Full array literal:\n')
    f.write(array_literal)
print('Wrote extracted array literal to buywisely_pushblock_extracted_array_literal.txt')
