with open('my-node-app/templates/admin.html', encoding='utf-8') as f:
    for idx, line in enumerate(f, 1):
        if 'pagination' in line.lower() or 'renderpage' in line.lower() or 'currentpage' in line.lower():
            print(f"{idx}: {line.strip()[:100]}")
