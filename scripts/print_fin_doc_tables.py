import sys
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')

with open('my-node-app/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

import re
matches = re.findall(r'CREATE TABLE IF NOT EXISTS `?([a-zA-Z0-9_]+)`?\s*\((.*?)\)', code, re.DOTALL | re.IGNORECASE)
for name, body in matches:
    if any(k in name.lower() for k in ['financ', 'doc', 'sale', 'sold', 'chat']):
        print(f"TABLE {name}:")
        for line in body.strip().splitlines()[:10]:
            print("  ", line.strip())
