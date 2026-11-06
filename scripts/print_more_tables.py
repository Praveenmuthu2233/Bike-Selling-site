import sys
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
import os

with open('my-node-app/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

idx = code.find('TABLE: sold_bikes')
if idx != -1:
    print(code[idx:idx+4000])
else:
    # Look for enquiries
    idx2 = code.find('CREATE TABLE IF NOT EXISTS `enquiries`')
    print(code[idx2:idx2+2500])
