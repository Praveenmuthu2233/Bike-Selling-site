import os
import re

def update_admin_login():
    path = 'my-node-app/templates/adminLogin.html'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    content = content.replace('background: #070A10;', 'background: #F8FAFC;')
    content = content.replace('background: rgba(13, 17, 27, 0.95);', 'background: #FFFFFF;')
    content = content.replace('border: 1px solid rgba(255, 107, 0, 0.35);', 'border: 1px solid #E2E8F0;')
    content = content.replace('box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6);', 'box-shadow: 0 10px 30px rgba(0, 0, 0, 0.06);')
    content = content.replace('color: #ffffff;', 'color: #0F172A;')
    content = content.replace('color: #fff;', 'color: #172033;')
    content = content.replace('background: #0A0E18;', 'background: #FFFFFF;')
    content = content.replace('border: 1px solid rgba(255, 255, 255, 0.12);', 'border: 1px solid #CBD5E1;')
    content = content.replace('background: rgba(255, 107, 0, 0.15);', 'background: #EFF6FF;')
    content = content.replace('border: 1px solid rgba(255, 107, 0, 0.4);', 'border: 1px solid #BFDBFE;')
    content = content.replace('color: #ff6b00;', 'color: #2563EB;')
    content = content.replace('linear-gradient(135deg, #FF6B00 0%, #E05300 100%)', 'linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%)')
    content = content.replace('background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.35); color: #fca5a5;', 'background: #FEF2F2; border: 1px solid #FECACA; color: #DC2626;')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated adminLogin.html")

def update_privacy_and_disclaimer():
    for fn in ['my-node-app/templates/privacy.html', 'my-node-app/templates/disclaimer.html']:
        with open(fn, 'r', encoding='utf-8') as f:
            content = f.read()

        content = content.replace('color: #FFFFFF;', 'color: #0F172A;')
        content = content.replace('color: #fff;', 'color: #0F172A;')
        content = content.replace('color: #E2E8F0;', 'color: #475569;')
        content = content.replace('linear-gradient(135deg, rgba(255,107,0,0.1) 0%, rgba(15,23,42,0.95) 100%)', '#EFF6FF')
        content = content.replace('border: 1px solid rgba(255,107,0,0.3);', 'border: 1px solid #BFDBFE;')
        content = content.replace('background: rgba(255, 107, 0, 0.08);', 'background: #EFF6FF;')

        with open(fn, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Updated:", fn)

def update_index_html():
    path = 'my-node-app/templates/index.html'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    content = content.replace('font-size: 1.75rem; font-weight: 800; font-family: var(--font-display); color: #FFF;', 'font-size: 1.75rem; font-weight: 800; font-family: var(--font-display); color: #0F172A;')
    content = content.replace('font-family: var(--font-display); font-size: 1.3rem; font-weight: 800; color: #FFF;', 'font-family: var(--font-display); font-size: 1.3rem; font-weight: 800; color: #0F172A;')
    content = content.replace('background: linear-gradient(135deg, rgba(255, 107, 0, 0.12) 0%, rgba(18, 24, 36, 0.95) 100%);', 'background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);')
    content = content.replace('background: linear-gradient(to top, rgba(11,15,23,0.95), transparent);', 'background: linear-gradient(to top, rgba(248,250,252,0.95), transparent);')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated index.html")

def update_enquiry_details():
    path = 'my-node-app/templates/enquiry-bike-details.html'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    content = content.replace('font-size: 2rem; font-weight: 800; color: #FFF;', 'font-size: 2rem; font-weight: 800; color: #0F172A;')
    content = content.replace('background: #000;', 'background: #F1F5F9;')
    content = content.replace('color: #FFF;', 'color: #0F172A;')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated enquiry-bike-details.html")

def update_contact_html():
    path = 'my-node-app/templates/contact.html'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    content = content.replace('color: #FFF;', 'color: #0F172A;')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated contact.html")

if __name__ == '__main__':
    update_admin_login()
    update_privacy_and_disclaimer()
    update_index_html()
    update_enquiry_details()
    update_contact_html()
