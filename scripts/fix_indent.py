app_path = "my-node-app/app.py"
with open(app_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
skip = False
for idx, line in enumerate(lines):
    if "if not session_id:" in line and idx + 1 < len(lines) and "session_id = len(store)" in lines[idx+1]:
        new_lines.append("    if not session_id:\n")
        new_lines.append("        session_id = int(datetime.datetime.utcnow().timestamp())\n")
        skip = True
        continue
    if skip:
        if "cookie_val = " in line:
            skip = False
            new_lines.append(line)
        continue
    new_lines.append(line)

with open(app_path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("Fixed session_id assignment")
