import os
for root, dirs, files in os.walk('.'):
    if any(x in root for x in ['.git', 'venv', '__pycache__', 'node_modules']):
        continue
    for f in files:
        if f.endswith(('.py', '.html', '.js', '.json')):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                c = fp.read()
                if '744800125665' in c:
                    print(f'{p}: contains client id')
