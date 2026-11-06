import sys
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
import os
import re

for fn in ['my-node-app/app.py', 'db.py', 'sql/init.sql', 'my-node-app/db.py']:
    if os.path.exists(fn):
        with open(fn, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        tables = re.findall(r'CREATE TABLE(?:\s+IF NOT EXISTS)?\s+`?([a-zA-Z0-9_]+)`?', text, re.IGNORECASE)
        print(f"{fn} defines tables:", set(tables))
