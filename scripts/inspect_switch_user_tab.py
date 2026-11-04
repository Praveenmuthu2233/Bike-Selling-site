with open('my-node-app/templates/profile.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'function switchUserTab' in line:
        print(f"switchUserTab at line {i+1}:")
        for j in range(i, min(i+35, len(lines))):
            print(f"  {j+1}: {lines[j].strip()}")
