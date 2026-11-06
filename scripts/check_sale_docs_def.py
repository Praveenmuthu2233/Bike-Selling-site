with open('my-node-app/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

idx = code.find('sale_documents')
print("idx:", idx)
idx_create = code.find('CREATE TABLE IF NOT EXISTS `sale_documents`')
if idx_create != -1:
    print(code[idx_create:idx_create+1200])
else:
    idx_create2 = code.find('sale_documents (')
    print("idx_create2:", idx_create2)
    if idx_create2 != -1:
        print(code[idx_create2-30:idx_create2+1200])
