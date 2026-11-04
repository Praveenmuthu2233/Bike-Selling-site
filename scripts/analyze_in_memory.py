import re

with open('my-node-app/app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

occurrences = []
for idx, line in enumerate(lines, 1):
    if 'IN_MEMORY_STORE' in line:
        occurrences.append((idx, line.strip()))

print(f"Total occurrences of IN_MEMORY_STORE: {len(occurrences)}")
for idx, text in occurrences:
    print(f"{idx}: {text[:120]}")
