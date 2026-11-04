import os

for root, dirs, files in os.walk('.'):
    if any(x in root for x in ['.git', 'venv', '__pycache__', 'node_modules']):
        continue
    for f in files:
        if f.endswith('.py') and not f.startswith('test') and 'script' not in root:
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                c = fp.read()
                if 'get_db' in c or 'mysql.connector' in c or 'DB_HOST' in c:
                    print(f'{p}: contains db logic')
