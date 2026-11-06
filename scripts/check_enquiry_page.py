import sys
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')

with open('my-node-app/templates/enquiry-bike-details.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'.{0,50}enquiry.{0,100}', text, re.IGNORECASE)
for m in matches[:20]:
    print(m.strip())
