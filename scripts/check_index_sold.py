with open('my-node-app/templates/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'sold', text, re.IGNORECASE)]
print(f"Total occurrences of sold in index.html: {len(matches)}")
for m in matches:
    print(text[m-30:m+80].replace('\n', ' '))
