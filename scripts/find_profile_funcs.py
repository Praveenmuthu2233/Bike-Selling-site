with open('my-node-app/templates/profile.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'loadUserNegotiations' in l or 'loadUserEnquiries' in l or 'loadFavorites' in l:
        print(f"Line {i+1}: {l.strip()[:60]}")
