with open('my-node-app/templates/enquiry-bike-details.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'.{0,50}(?:profile|chat|messages).{0,50}', text, re.IGNORECASE)
for m in matches[:10]:
    print(m.strip())
