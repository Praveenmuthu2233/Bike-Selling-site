with open("my-node-app/static/api.js", "r", encoding="utf-8") as f:
    text = f.read()

print("api.js length:", len(text))
print(text[:2000])
