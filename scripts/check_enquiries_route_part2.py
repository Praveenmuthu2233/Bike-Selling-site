with open('my-node-app/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

idx = code.find('/api/enquiries", methods=["GET", "POST"]')
print(code[idx+800:idx+2500])
