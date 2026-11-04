with open('my-node-app/static/auth.js', 'r', encoding='utf-8') as f:
    text = f.read()

for idx, line in enumerate(text.splitlines(), 1):
    if 'demoLogin' in line or 'Demo Rider' in line:
        print(f"L{idx}: {line}")
