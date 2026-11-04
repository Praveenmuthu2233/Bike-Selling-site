with open('my-node-app/templates/profile.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for j in range(1533, 1620):
    # sanitize characters that might cause encoding error on stdout
    line_clean = lines[j].rstrip().replace('\u20b9', 'INR')
    print(f"{j+1}: {line_clean}")
