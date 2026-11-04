import os

files = [
    'my-node-app/templates/admin.html',
    'my-node-app/templates/profile.html',
    'my-node-app/static/adminStyle.css',
    'my-node-app/static/profileStyle.css'
]

for p in files:
    if os.path.exists(p):
        with open(p, encoding='utf-8') as f:
            lines = len(f.readlines())
        print(f"{p}: {lines} lines, {os.path.getsize(p):,} bytes")
    else:
        print(f"{p}: NOT FOUND")
