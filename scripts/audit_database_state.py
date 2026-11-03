import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_DIR = os.path.join(BASE_DIR, "my-node-app")
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from app import get_db

print("=== SMR MOTORS: TiDB CLOUD AUDIT ===")
conn = get_db()
if not conn:
    print("[ERROR] Cannot connect to TiDB Cloud!")
    sys.exit(1)

cur = conn.cursor()
cur.execute("SHOW TABLES")
tables = [r[0] for r in cur.fetchall()]

print(f"Total tables in database: {len(tables)}")
for t in sorted(tables):
    cur.execute(f"SELECT COUNT(*) FROM `{t}`")
    count = cur.fetchone()[0]
    print(f"  - {t}: {count} records")

cur.close()
conn.close()
print("=== AUDIT COMPLETE ===")
