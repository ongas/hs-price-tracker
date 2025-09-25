# Utility to dump region around parse error in normalized array literal
with open('buywisely_pushblock_extracted_array_literal.txt', 'r', encoding='utf-8') as f:
    s = f.read()
    pos = 2676
    print('200 chars before error:', s[max(0, pos-200):pos])
    print('200 chars after error:', s[pos:pos+200])
    print('Error region:', s[max(0, pos-20):pos+20])
