# Diagnostic utility for BuyWisely push block parsing
# This script will print the first 4000 characters and attempt to identify problematic regions for parser improvement.

with open('buywisely_pushblock_diag_full.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    for line in lines:
        if line.strip().startswith('['):
            push_block = line.strip()
            break
    else:
        raise ValueError('No push block found in file!')

print('First 4000 chars:')
print(push_block[:4000])

# Print a region around the first parse error (char 2678)
err_idx = 2678
print('\nContext around parse error:')
print(push_block[err_idx-100:err_idx+100])

# Print the last 500 chars
print('\nLast 500 chars:')
print(push_block[-500:])
