backend_file = 'my-node-app/app.py'
with open(backend_file, 'r', encoding='utf-8') as f:
    content = f.read()

target = 'limit = max(1, int(request.args.get("limit", 9)))'
replacement = 'limit = max(1, min(int(request.args.get("limit", 6)), 50))'

if target in content:
    content = content.replace(target, replacement, 1)
    with open(backend_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated default sold limit to 6 in app.py")
else:
    print("Target limit line not found")
