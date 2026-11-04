import sys

sys.stdout.reconfigure(encoding='utf-8')
with open('my-node-app/static/auth.js', encoding='utf-8') as f:
    for idx, line in enumerate(f, 1):
        if 'demologin' in line.lower() or 'demo-google' in line.lower():
            print(f"{idx}: {line.strip()[:100]}")
