with open('my-node-app/templates/SoldOutPage.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('loadSoldBikes')
print(text[idx+500:idx+1500])
