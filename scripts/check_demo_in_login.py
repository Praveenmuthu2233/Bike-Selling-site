import glob

for f in glob.glob('my-node-app/templates/*login*.html') + glob.glob('*login*.html'):
    with open(f, encoding='utf-8', errors='ignore') as fp:
        for idx, l in enumerate(fp, 1):
            if 'demo' in l.lower():
                print(f"{f}:{idx}: {l.strip()[:100]}")
