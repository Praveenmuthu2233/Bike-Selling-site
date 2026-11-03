with open('my-node-app/app.py', 'r', encoding='utf-8') as f:
    c = f.read()

target = '@app.route("/api/bikes/sold", methods=["GET"])'
replacement = '@app.route("/api/bikes/sold", methods=["GET"])\n@app.route("/api/sold-bikes", methods=["GET"])'

assert target in c, "target not found"
c = c.replace(target, replacement, 1)

with open('my-node-app/app.py', 'w', encoding='utf-8') as f:
    f.write(c)

print("Added /api/sold-bikes alias.")
