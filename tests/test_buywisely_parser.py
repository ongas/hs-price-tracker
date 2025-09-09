

from services.buywisely.parser import parse_product

def test_parser():
    with open('/tmp/buywisely_page.html', 'r', encoding='utf-8') as f:
        html = f.read()
    result = parse_product(html, product_id=None, recency_days=7)
    print("Parsed result:")
    for key, value in result.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    test_parser()
