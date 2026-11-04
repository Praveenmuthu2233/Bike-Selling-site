with open('my-node-app/static/marketplace.js', 'r', encoding='utf-8') as f:
    text = f.read()

lines = text.splitlines()
for idx, line in enumerate(lines, 1):
    if 'loadBikes' in line or 'renderBikes' in line or 'empty' in line.lower() or 'error' in line.lower():
        print(f"L{idx}: {line[:100]}")
