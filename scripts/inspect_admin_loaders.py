with open('my-node-app/templates/admin.html', encoding='utf-8') as f:
    for idx, line in enumerate(f, 1):
        if any(term in line for term in ['loadAdminStaff', 'loadContactMessages', 'loadAdminMessages', 'loadAuditLogs', 'loadAdminChat', 'loadChat']):
            print(f"{idx}: {line.strip()[:100]}")
