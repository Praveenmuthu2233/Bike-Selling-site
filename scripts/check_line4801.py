app_path = "my-node-app/app.py"
with open(app_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx in range(4790, 4810):
    if idx < len(lines):
        print(f"L{idx+1}: {repr(lines[idx])}")
