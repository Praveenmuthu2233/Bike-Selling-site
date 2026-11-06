with open('my-node-app/templates/userLogin.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
styles = re.findall(r'style="[^"]*?"', text, re.IGNORECASE)
for s in styles[:10]:
    print("  ", s)
