with open('my-node-app/templates/admin.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('loadSoldOutBikes')
if idx == -1: idx = text.find('renderSold')
if idx == -1: idx = text.find('sold-table-body')
print(text[idx:idx+1500])
