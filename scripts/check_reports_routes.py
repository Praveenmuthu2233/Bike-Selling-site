with open("my-node-app/app.py", "r", encoding="utf-8") as f:
    for idx, line in enumerate(f, 1):
        if "/api/admin/reports" in line:
            print(f"L{idx}: {line.strip()}")
