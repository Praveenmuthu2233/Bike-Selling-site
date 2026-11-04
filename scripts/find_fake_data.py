import os, re

keywords = ['demo', 'mock', 'fake', 'dummy', 'sample', 'in_memory_store', 'fallback_data', 'default_bikes', 'seed']
results = {}

for root, dirs, files in os.walk('.'):
    if any(p in root for p in ['.git', 'node_modules', '.venv', '__pycache__', 'tests']):
        continue
    for f in files:
        if f.endswith(('.py', '.js', '.html')) and not f.startswith('test_'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8', errors='ignore') as fp:
                for idx, line in enumerate(fp, 1):
                    for kw in keywords:
                        if re.search(r'\b' + kw + r'\b', line, re.IGNORECASE):
                            line_s = line.strip()
                            if len(line_s) < 140:
                                results.setdefault(path, []).append((idx, kw, line_s))
                            break

for path, matches in sorted(results.items()):
    print(f"\n=== {path} ({len(matches)} matches) ===")
    for idx, kw, line in matches[:15]:
        print(f"  [{idx:4}] ({kw}): {line}")
    if len(matches) > 15:
        print(f"  ... and {len(matches) - 15} more matches")
