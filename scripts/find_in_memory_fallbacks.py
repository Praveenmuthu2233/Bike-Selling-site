with open('my-node-app/app.py', 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f, 1):
        if 'IN_MEMORY_STORE' in line:
            print(f'{idx}: {line.strip()[:110]}')
