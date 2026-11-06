import os
import glob
import re

html_files = glob.glob('my-node-app/templates/*.html')
dark_patterns = [
    r'background:\s*#0[0-9a-fA-F]{5}',
    r'background:\s*#1[0-9a-fA-F]{5}',
    r'background-color:\s*#0[0-9a-fA-F]{5}',
    r'background-color:\s*#1[0-9a-fA-F]{5}',
    r'color:\s*#fff',
    r'color:\s*#FFF',
    r'color:\s*white',
]

results = {}
for h in html_files:
    with open(h, 'r', encoding='utf-8') as f:
        content = f.read()
    found = []
    for p in dark_patterns:
        m = re.findall(p, content, re.IGNORECASE)
        if m:
            found.extend(m)
    if found:
        results[os.path.basename(h)] = len(found)

for k, v in sorted(results.items(), key=lambda x: x[1], reverse=True):
    print(f"{k}: {v} dark style occurrences")
