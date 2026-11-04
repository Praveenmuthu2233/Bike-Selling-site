with open("my-node-app/app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

fallback_blocks = []
current_func = ""
for idx, line in enumerate(lines, 1):
    if line.startswith("def ") or line.startswith("@app.route"):
        current_func = line.strip()
    if "IN_MEMORY_STORE" in line:
        fallback_blocks.append((idx, current_func, line.strip()))

print(f"Total fallback lines: {len(fallback_blocks)}")
funcs_seen = set()
for idx, func, line in fallback_blocks:
    if func not in funcs_seen:
        funcs_seen.add(func)
        print(f"\nFunction: {func}")
    print(f"  Line {idx}: {line[:100]}")
