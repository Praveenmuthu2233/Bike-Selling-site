with open('my-node-app/templates/admin.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('id="tab-soldout-bikes"')
print(text[idx:idx+1500])
