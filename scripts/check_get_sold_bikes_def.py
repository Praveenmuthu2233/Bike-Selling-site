with open('my-node-app/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

idx = code.find('def get_sold_bikes_api():')
print(code[idx:idx+1500])
