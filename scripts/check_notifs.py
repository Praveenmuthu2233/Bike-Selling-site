with open('my-node-app/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

import re
matches = re.findall(r'def\s+create_notification[^\)]*\):', code)
print("create_notification:", matches)
if not matches:
    matches = re.findall(r'INSERT INTO notifications', code, re.IGNORECASE)
    print("INSERT INTO notifications count:", len(matches))
