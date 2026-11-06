import sys
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')

with open('my-node-app/templates/admin.html', 'r', encoding='utf-8') as f:
    code = f.read()

idx = code.find('function loadSoldOutBikesView(')
print(code[idx+3200:idx+4500])
