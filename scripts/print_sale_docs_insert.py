with open('my-node-app/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

idx = code.find('INSERT INTO sale_documents')
print(code[idx-200:idx+600])
