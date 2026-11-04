import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("my-node-app/app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for start_line in [3585, 3665, 3755, 4585]:
    print(f"\n=== Function around {start_line} ===")
    for j in range(start_line - 1, min(len(lines), start_line + 30)):
        print(f"{j+1}: {lines[j].rstrip()}")
        if lines[j].startswith("def ") or lines[j].startswith("@app.route"):
            if j > start_line + 5:
                break
