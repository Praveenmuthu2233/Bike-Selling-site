import sys
sys.stdout.reconfigure(encoding='utf-8')

app_path = "my-node-app/app.py"
with open(app_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

fixed = 0
for idx, line in enumerate(lines):
    if line.startswith("log_admin_action("):
        lines[idx] = "    " + line
        fixed += 1
        print(f"Fixed unindented log_admin_action at line {idx+1}")

with open(app_path, "w", encoding="utf-8") as f:
    f.writelines(lines)

print(f"Total fixed: {fixed}")
