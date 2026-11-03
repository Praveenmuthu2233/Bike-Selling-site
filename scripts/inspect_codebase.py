import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('my-node-app/app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    print(''.join(lines[1840:1855]))
