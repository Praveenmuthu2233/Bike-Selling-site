import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("my-node-app/app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines, 1):
    if "IN_MEMORY_STORE" in line and idx != 205:
        print(f"\n--- Line {idx} ---")
        for j in range(max(0, idx - 5), min(len(lines), idx + 5)):
            print(f"{j+1}: {lines[j].rstrip()}")
