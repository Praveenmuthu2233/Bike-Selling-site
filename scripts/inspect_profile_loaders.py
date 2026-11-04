with open('my-node-app/templates/profile.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("loadUserNegotiations around line 1417-1440:")
for j in range(1416, 1445):
    print(f"  {j+1}: {lines[j].strip()}")

print("\nloadUserEnquiries around line 1534-1560:")
for j in range(1533, 1560):
    print(f"  {j+1}: {lines[j].strip()}")
