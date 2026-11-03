import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_DIR = os.path.join(BASE_DIR, "my-node-app")
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from app import get_db

conn = get_db()
cursor = conn.cursor()
cursor.execute("SHOW TABLES LIKE 'chat_%'")
tables = [r[0] for r in cursor.fetchall()]
print("[Chat Migration] Verified Chat tables in TiDB:", tables)

for t in tables:
    cursor.execute(f"DESCRIBE {t}")
    cols = [col[0] for col in cursor.fetchall()]
    print(f"  - {t}: {', '.join(cols)}")

cursor.close()
conn.close()
print("[Chat Migration] Completed successfully.")
