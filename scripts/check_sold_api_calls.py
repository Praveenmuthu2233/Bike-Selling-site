with open('my-node-app/templates/SoldOutPage.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'/api/[a-zA-Z0-9_\-\/]+', text)
print("SoldOutPage API calls:", set(matches))

with open('my-node-app/templates/index.html', 'r', encoding='utf-8') as f:
    text_index = f.read()
matches_index = re.findall(r'/api/[a-zA-Z0-9_\-\/]+', text_index)
print("index.html API calls:", set(matches_index))
