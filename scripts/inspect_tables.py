import sys
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
import os
import re

with open('my-node-app/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Look for table creation queries
table_queries = re.findall(r'CREATE TABLE IF NOT EXISTS\s+([a-zA-Z0-9_]+)\s*\((.*?)\);', code, re.DOTALL | re.IGNORECASE)
print(f"Tables defined via CREATE TABLE IF NOT EXISTS: {len(table_queries)}")
for tname, cols in table_queries:
    print(f"\n--- TABLE: {tname} ---")
    for line in cols.strip().splitlines()[:15]:
        print("  ", line.strip())
