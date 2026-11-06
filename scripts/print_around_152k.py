with open('my-node-app/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

idx = 152118
print(code[idx-300:idx+1500])
