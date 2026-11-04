import os

for path in ['.env', 'my-node-app/.env', '.env.example', 'my-node-app/.env.example']:
    if os.path.exists(path):
        print(f"=== {path} ===")
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line_str = line.strip()
                if any(k in line_str for k in ['DB_', 'TIDB_', 'DATABASE_URL', 'MYSQL_']):
                    if 'PASSWORD' in line_str:
                        parts = line_str.split('=', 1)
                        print(f"{parts[0]}=*** (length: {len(parts[1]) if len(parts) > 1 else 0})")
                    else:
                        print(line_str)
