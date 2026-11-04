app_path = "my-node-app/app.py"
with open(app_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

lines[4720] = "    " + lines[4720]

with open(app_path, "w", encoding="utf-8") as f:
    f.writelines(lines)

print("Indented line 4721")
