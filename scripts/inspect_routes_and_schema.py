import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import re
import os

with open('my-node-app/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

routes = re.findall(r'@app\.route\([\'\"]([^\'\"]+)[\'\"](?:,\s*methods=\[([^\]]+)\])?', code)
print(f"Total routes found: {len(routes)}")
for path, methods in routes:
    methods = methods if methods else "'GET'"
    if any(k in path.lower() for k in ['enquir', 'sold', 'doc', 'bike', 'accept', 'negotiat']):
        print(f"  {path:45} [{methods}]")
