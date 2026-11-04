with open("my-node-app/app.py", "r", encoding="utf-8") as f:
    for idx, line in enumerate(f, 1):
        if "tidbStatus" in line or "/api/config" in line:
            print(f"L{idx}: {line.strip()}")
