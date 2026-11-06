with open('my-node-app/templates/admin.html', 'r', encoding='utf-8') as f:
    code = f.read()

idx = code.find('function loadSoldOutBikesView(')
print(code[idx+2000:idx+3500])
