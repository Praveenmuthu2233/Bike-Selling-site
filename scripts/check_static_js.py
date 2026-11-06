import glob
import re

for fn in glob.glob('my-node-app/static/*.js'):
    with open(fn, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()
    if 'enquiry' in text.lower():
        print("Found enquiry in:", fn)
        matches = re.findall(r'.{0,40}submitenquiry.{0,60}', text, re.IGNORECASE)
        for m in matches:
            print("  ", m.strip())
