with open('my-node-app/templates/admin.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("Staff Activity func lines 3750-3775:")
for j in range(3749, 3775):
    print(f"  {j+1}: {lines[j].strip()}")
