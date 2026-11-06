with open('my-node-app/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

idx = code.find('/api/chat/conversations')
print(code[idx:idx+2500])
