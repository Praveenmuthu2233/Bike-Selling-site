import os
import sys
from dotenv import load_dotenv

# Load env from my-node-app/.env and .env
load_dotenv('my-node-app/.env')
load_dotenv('.env')

sys.path.insert(0, 'my-node-app')
import db

conn = db.get_db()
if not conn:
    print("DB connection returned None!")
    sys.exit(1)

cursor = conn.cursor(dictionary=True)
cursor.execute("SELECT id, username, full_name, email, phone, role, is_active, created_at, last_login FROM admins")
rows = cursor.fetchall()
print(f"Total admin rows: {len(rows)}")
for r in rows:
    print(r)

cursor.close()
conn.close()
