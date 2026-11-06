with open('my-node-app/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

idx = code.find('/api/admin/sold-bikes/<int:bike_id>')
print(code[idx-50:idx+1500])
