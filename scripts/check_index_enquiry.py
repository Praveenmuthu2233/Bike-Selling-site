with open('my-node-app/templates/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
idx = text.find('enquiry-modal')
print(text[idx-200:idx+800])
