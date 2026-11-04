import os

for root, dirs, files in os.walk('.'):
    # Skip noisy directories
    dirs[:] = [d for d in dirs if d not in ('node_modules', '.git', '__pycache__', '.venv', 'dist', 'build', '.gemini')]
    for f in files:
        if f.endswith(('.py', '.env', '.json', '.txt', '.md', '.yaml', '.yml', '.js')):
            path = os.path.join(root, f)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as fp:
                    for idx, line in enumerate(fp, 1):
                        if 'clever-cloud' in line.lower() or 'bnyo89' in line.lower():
                            print(f"{path}:{idx}: {line.strip()[:120]}")
            except Exception:
                pass
