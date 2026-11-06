import sys
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
import os

with open('my-node-app/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

import re
idx = code.find('def initialize_database(')
if idx != -1:
    print(code[idx:idx+3500])
else:
    print("initialize_database not found!")
