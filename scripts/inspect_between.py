with open('my-node-app/templates/profile.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for j in range(1495, 1535):
    print(f"{j+1}: {lines[j].rstrip()}")
