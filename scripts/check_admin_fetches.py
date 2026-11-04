with open("my-node-app/templates/admin.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

print("admin.html total lines:", len(lines))
for idx, line in enumerate(lines, 1):
    if "fetch(" in line or "apiRequest(" in line:
        print(f"Line {idx}: {line.strip()[:100]}")
