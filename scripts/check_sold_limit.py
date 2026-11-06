with open('my-node-app/templates/SoldOutPage.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('soldLimit')
print(text[idx-50:idx+150])
