with open('my-node-app/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

idx = code.find('def enquiries_api():')
end_idx = code.find('\n@app.route', idx)
print(code[idx:end_idx])
