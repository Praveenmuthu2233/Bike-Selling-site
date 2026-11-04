with open('my-node-app/templates/admin.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("Staff func lines 3725-3745:")
for j in range(3724, 3745):
    print(f"  {j+1}: {lines[j].strip()}")

print("\nMessages func lines 3895-3910:")
for j in range(3894, 3910):
    print(f"  {j+1}: {lines[j].strip()}")
