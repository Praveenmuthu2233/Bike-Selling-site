import os

terms = [
    'hunter 350', 'dapper ash', 'demo rider', 'sample enquiry', 'sample bike',
    'mock', 'placeholder', 'dummy', 'fake', 'test-mock-token', 'demo-google'
]

results = []
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ('node_modules', '.git', '__pycache__', '.venv')]
    for f in files:
        if f.endswith(('.py', '.js', '.html', '.json')):
            path = os.path.join(root, f)
            try:
                with open(path, encoding='utf-8', errors='ignore') as fp:
                    for idx, line in enumerate(fp, 1):
                        l_lower = line.lower()
                        for t in terms:
                            if t in l_lower and 'test_' not in f:
                                results.append((path, idx, t, line.strip()[:110]))
                                break
            except Exception:
                pass

print(f"Total findings: {len(results)}")
for r in results[:40]:
    print(f"{r[0]}:{r[1]} [{r[2]}] -> {r[3]}")
