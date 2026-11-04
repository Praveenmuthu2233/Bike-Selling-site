with open('my-node-app/templates/admin.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'async function loadAdminStaff' in line or 'async function loadAdminMessages' in line or 'async function loadStaffActivity' in line:
        print(f"Line {i+1}: {line.strip()}")
        for j in range(i, min(i+15, len(lines))):
            print(f"  {j+1}: {lines[j].strip()}")
