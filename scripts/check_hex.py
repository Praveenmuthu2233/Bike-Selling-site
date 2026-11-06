import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

with open('my-node-app/templates/SoldOutPage.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'.{0,30}#[0-9a-fA-F]{3,6}.{0,30}', text)
for m in matches:
    print("SoldOutPage:", m.strip())

with open('my-node-app/templates/about.html', 'r', encoding='utf-8') as f:
    text = f.read()
matches = re.findall(r'.{0,30}#[0-9a-fA-F]{3,6}.{0,30}', text)
for m in matches:
    print("about:", m.strip())
