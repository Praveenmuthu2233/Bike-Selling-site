with open('my-node-app/templates/admin.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
funcs = re.findall(r'function\s+([a-zA-Z0-9_]*chat[a-zA-Z0-9_]*)', text, re.IGNORECASE)
for fn in set(funcs):
    print("Chat function in admin.html:", fn)
