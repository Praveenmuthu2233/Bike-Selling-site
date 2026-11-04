with open('my-node-app/templates/profile.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("Navbar lines 440-465:")
for j in range(439, 465):
    print(f"  {j+1}: {lines[j].strip()}")
