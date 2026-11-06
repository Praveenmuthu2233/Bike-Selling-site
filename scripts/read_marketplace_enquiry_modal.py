import sys
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')

with open('my-node-app/static/marketplace.js', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('function openEnquiryModal(')
print(text[idx:idx+1200])
