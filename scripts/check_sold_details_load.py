import sys
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')

with open('my-node-app/templates/sold-bike-details.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('loadBikeDetails')
if idx == -1: idx = text.find('fetch(')
if idx == -1: idx = text.find('apiRequest')
print(text[idx-50:idx+1500])
