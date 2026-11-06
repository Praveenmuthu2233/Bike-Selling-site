import sys
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')

with open('my-node-app/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

idx = code.find('def admin_approve_bike(')
end_idx = code.find('\n@app.route', idx)
print(code[idx:end_idx])
