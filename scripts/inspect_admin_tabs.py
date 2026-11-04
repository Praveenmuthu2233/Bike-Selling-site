with open('my-node-app/templates/admin.html', encoding='utf-8') as f:
    for idx, line in enumerate(f, 1):
        if 'id="tab-messages"' in line or 'id="tab-staff"' in line or 'admin-staff-tbody' in line or 'admin-messages-tbody' in line:
            print(f"{idx}: {line.strip()[:100]}")
