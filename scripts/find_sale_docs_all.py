import re
with open('my-node-app/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

matches = [m.start() for m in re.finditer(r'sale_documents', code)]
print(f"Total occurrences of sale_documents: {len(matches)}")
for m in matches:
    print(code[m-50:m+100].replace('\n', ' '))
