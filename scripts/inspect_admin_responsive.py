with open('my-node-app/templates/admin.html', encoding='utf-8') as f:
    for idx, line in enumerate(f, 1):
        if '@media' in line or 'hamburger' in line.lower() or 'sidebar-toggle' in line.lower() or 'sidebar-open' in line.lower():
            print(f"{idx}: {line.strip()[:100]}")
