with open('my-node-app/app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if '@app.route("/api/admin/chat/conversations"' in l or "@app.route('/api/admin/chat/conversations'" in l:
        print(f"Line {i+1}:")
        for j in range(i, min(i+40, len(lines))):
            print(f"  {j+1}: {lines[j].rstrip()}")
        break
