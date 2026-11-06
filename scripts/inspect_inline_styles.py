import glob
import re

files = ['my-node-app/templates/privacy.html', 'my-node-app/templates/disclaimer.html', 'my-node-app/templates/sold-bike-details.html', 'my-node-app/templates/adminLogin.html', 'my-node-app/templates/index.html', 'my-node-app/templates/contact.html', 'my-node-app/templates/enquiry-bike-details.html']

for fn in files:
    with open(fn, 'r', encoding='utf-8') as f:
        text = f.read()
    print("=== File:", fn)
    styles = re.findall(r'style="[^"]*?(?:background|color:[^"]*?#fff)[^"]*?"', text, re.IGNORECASE)
    for s in styles[:8]:
        print("  ", s)
