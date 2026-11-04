with open('my-node-app/templates/SoldOutPage.html', 'r', encoding='utf-8') as f:
    text = f.read()

for idx, line in enumerate(text.splitlines(), 1):
    if 'fetch' in line or 'apiRequest' in line or 'empty' in line.lower() or 'error' in line.lower():
        print(f"L{idx}: {line[:100]}")
