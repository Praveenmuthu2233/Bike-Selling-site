import subprocess

try:
    log = subprocess.check_output(['git', 'log', '-p', '-S', 'hH3EBvquLgqPWEo', '--', '.env', 'my-node-app/.env'], encoding='utf-8')
    print("Git search found changes:")
    for line in log.splitlines():
        if any(w in line for w in ['commit', 'TIDB_PASSWORD', 'DB_PASSWORD', 'hH3EBvquLgqPWEo']):
            print(line)
except Exception as e:
    print("Git search error:", e)
