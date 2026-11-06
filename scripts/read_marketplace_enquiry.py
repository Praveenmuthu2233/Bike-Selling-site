with open('my-node-app/static/marketplace.js', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('submitEnquiry')
print(text[idx-300:idx+800])
