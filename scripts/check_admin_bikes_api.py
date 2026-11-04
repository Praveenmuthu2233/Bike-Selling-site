with open("my-node-app/app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines, 1):
    if "def admin_bikes_api" in line:
        for j in range(idx - 1, min(idx + 45, len(lines))):
            print(f"{j+1}: {lines[j].rstrip()}")
        break
