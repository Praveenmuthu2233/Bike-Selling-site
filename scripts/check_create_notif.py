with open('my-node-app/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

idx = code.find('def create_notification(')
print(code[idx:idx+1000])
