import sys
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
import glob
import re

for fn in glob.glob('my-node-app/templates/*.html'):
    with open(fn, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()
    if 'enquiry' in text.lower():
        fns = re.findall(r'function\s+([a-zA-Z0-9_]*enquiry[a-zA-Z0-9_]*)', text, re.IGNORECASE)
        modals = re.findall(r'id=[\'\"]([^\'\"]*enquiry[^\'\"]*)[\'\"]', text, re.IGNORECASE)
        print(f"File: {fn}")
        if fns: print("  Functions:", set(fns))
        if modals: print("  Elements with enquiry ID:", set(modals))
