import os

for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ('node_modules', '.git', '__pycache__')]
    for f in files:
        if f.endswith(('.sql', '.json', '.csv')) and not f.endswith('package.json') and not f.endswith('package-lock.json'):
            p = os.path.join(root, f)
            print(f"{p} ({os.path.getsize(p)} bytes)")
