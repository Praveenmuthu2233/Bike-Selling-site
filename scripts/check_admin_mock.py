with open('my-node-app/templates/admin.html', 'r', encoding='utf-8') as f:
    text = f.read()

for idx, line in enumerate(text.splitlines(), 1):
    low = line.lower()
    if ('mock' in low or 'dummy' in low or 'fake' in low or 'sample' in low or 'demo rider' in low) and not line.strip().startswith('<!--'):
        print(f"L{idx}: {line.strip()[:100]}")
