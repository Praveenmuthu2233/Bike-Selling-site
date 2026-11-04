import glob

for p in glob.glob('scripts/*.py') + glob.glob('tests/*.py'):
    with open(p, encoding='utf-8', errors='ignore') as f:
        for idx, l in enumerate(f, 1):
            if any(term in l for term in ['hH3E', 'tidbcloud', 'isrgrootx1']):
                print(f"{p}:{idx}: {l.strip()[:100]}")
