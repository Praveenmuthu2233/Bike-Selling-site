import re

def update_admin():
    path = 'my-node-app/templates/admin.html'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace orange accents with blue accents in chat style
    content = content.replace('#ea580c', '#2563EB')
    content = content.replace('#f97316', '#1D4ED8')
    content = content.replace('rgba(234, 88, 12,', 'rgba(37, 99, 235,')
    content = content.replace('rgba(249, 115, 22,', 'rgba(37, 99, 235,')

    # Update active conversation item border and highlight
    content = content.replace('border-left: 3px solid #ea580c;', 'border-left: 3px solid #2563EB;')
    content = content.replace('background: #ea580c;', 'background: #2563EB;')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated admin.html successfully")

if __name__ == '__main__':
    update_admin()
