with open('my-node-app/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

idx = code.find('sale-documents')
if idx != -1:
    print(code[idx-100:idx+800])
else:
    print("sale-documents not found")
