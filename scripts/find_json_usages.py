import os

for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ('node_modules', '.git', '__pycache__')]
    for f in files:
        if f.endswith(('.py', '.js', '.html')):
            p = os.path.join(root, f)
            try:
                for idx, line in enumerate(open(p, encoding='utf-8', errors='ignore'), 1):
                    if 'data.json' in line or 'category.json' in line or 'galary.json' in line:
                        print(f"{p}:{idx}: {line.strip()[:100]}")
            except Exception:
                pass
