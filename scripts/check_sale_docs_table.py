with open('my-node-app/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

import re
matches = re.findall(r'.{0,50}sale_documents.{0,100}', code)
for m in matches[:15]:
    print(m.strip())
