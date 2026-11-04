import os

for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ('node_modules', '.git', '__pycache__')]
    for f in files:
        if f.endswith(('.py', '.env', '.json', '.txt', '.md', '.yaml', '.yml', '.js', '.html')):
            path = os.path.join(root, f)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as fp:
                    for idx, line in enumerate(fp, 1):
                        if 'hH3E' in line:
                            print(f"{path}:{idx}: {line.strip()[:100]}")
            except Exception:
                pass
