with open('my-node-app/app.py', encoding='utf-8') as f:
    for idx, line in enumerate(f, 1):
        if any(term in line.lower() for term in ['seed', 'sample', 'dummy', 'initial_', 'demo_']):
            print(f"{idx}: {line.strip()[:100]}")
