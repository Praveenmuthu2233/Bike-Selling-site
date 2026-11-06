with open('my-node-app/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

idx = code.find('def handle_enquiries():')
if idx == -1: idx = code.find('def create_enquiry(')
if idx == -1: idx = code.find('/api/enquiries')
print(code[idx:idx+1500])
