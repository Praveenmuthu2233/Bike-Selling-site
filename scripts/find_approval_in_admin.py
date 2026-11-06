def find_approval_in_admin():
    with open('my-node-app/templates/admin.html', 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f, 1):
            if any(k.lower() in line.lower() for k in ['openapprove', 'confirmapprove', 'publish motorcycle', 'confirm & publish', 'approvebike']):
                print(f"{idx}: {line.strip()}")

if __name__ == '__main__':
    find_approval_in_admin()
