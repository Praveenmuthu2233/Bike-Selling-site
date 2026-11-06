with open('my-node-app/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

idx = code.find('CREATE TABLE IF NOT EXISTS `enquiries`')
print(code[idx:idx+600])
