import sys
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
import os

with open('my-node-app/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

idx = code.find('def initialize_database(')
end_idx = code.find('def get_db(', idx)
if end_idx == -1: end_idx = idx + 15000

tables_section = code[idx:end_idx]
import re
creates = re.findall(r'CREATE TABLE IF NOT EXISTS `?([a-zA-Z0-9_]+)`?\s*\((.*?)\)\s*ENGINE', tables_section, re.DOTALL | re.IGNORECASE)
for t, cols in creates:
    print(f"\n==================== TABLE: {t} ====================")
    for l in cols.strip().splitlines():
        if not l.strip().startswith('INDEX') and not l.strip().startswith('KEY'):
            print("  ", l.strip())
