import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
p = r"C:\Users\COREI5 8THGEN\.gemini\antigravity\brain\a0275452-396f-403c-b255-8d8aa229d41f\tidb_full_website_integration_report.md"

if os.path.exists(p):
    with open(p, encoding='utf-8') as f:
        for idx, line in enumerate(f, 1):
            if any(k in line.lower() for k in ['table', 'bike', 'enquir', 'user', 'chat', 'schema', 'dummy', 'demo', 'hunter']):
                print(f"{idx}: {line.strip()[:100]}")
