with open('my-node-app/templates/SoldOutPage.html', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('background: rgba(30, 64, 175, 0.12); border: 1px solid rgba(59, 130, 246, 0.3);', 'background: #EFF6FF; border: 1px solid #BFDBFE;')
text = text.replace('color: #93C5FD;', 'color: #1D4ED8;')
text = text.replace('color:#34D399;', 'color:#16A34A;')

with open('my-node-app/templates/SoldOutPage.html', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated SoldOutPage.html")

with open('my-node-app/templates/about.html', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('font-weight: 700; color: #FFF;', 'font-weight: 700; color: #0F172A;')

with open('my-node-app/templates/about.html', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated about.html")
