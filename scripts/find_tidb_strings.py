import os
import re

for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ('node_modules', '.git', '__pycache__')]
    for f in files:
        if f.endswith(('.env', '.txt', '.py', '.md', '.json', '.sql')):
            p = os.path.join(root, f)
            try:
                for idx, line in enumerate(open(p, encoding='utf-8', errors='ignore'), 1):
                    if 'gateway01.ap-southeast-1' in line or 'tidbcloud' in line:
                        # Print line with masked password if any
                        print(f"{p}:{idx}: {line.strip()[:100]}")
            except Exception:
                pass
