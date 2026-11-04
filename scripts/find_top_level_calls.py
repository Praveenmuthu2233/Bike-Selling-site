with open("my-node-app/app.py", "r", encoding="utf-8") as f:
    for idx, line in enumerate(f, 1):
        # find calls to initialize_database() or get_db() at top level
        if "initialize_database" in line or ("get_db" in line and not line.strip().startswith("def")):
            print(f"L{idx}: {line.strip()}")
