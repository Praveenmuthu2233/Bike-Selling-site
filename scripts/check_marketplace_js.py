with open("my-node-app/static/marketplace.js", "r", encoding="utf-8") as f:
    text = f.read()

print("marketplace.js length:", len(text))
for line in text.splitlines():
    if "api" in line.lower() or "fetch" in line.lower() or "hero" in line.lower():
        print(line[:120])
