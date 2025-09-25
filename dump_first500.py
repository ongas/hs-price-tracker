# Utility to dump the first 500 chars of the normalized array literal for inspection
with open('buywisely_pushblock_extracted_array_literal.txt', 'r', encoding='utf-8') as f:
    s = f.read()
    print('First 500 chars:', s[:500])
    print('First 1000 chars:', s[:1000])
