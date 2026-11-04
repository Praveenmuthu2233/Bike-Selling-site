import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'my-node-app')
import app

conn = app.get_db()
if not conn:
    print("Failed to connect to TiDB Cloud!")
    sys.exit(1)

cur = conn.cursor(dictionary=True)
cur.execute('SHOW TABLES')
tables = [list(r.values())[0] for r in cur.fetchall()]
print(f"Total Tables in `smr_motors`: {len(tables)}\n")
for t in sorted(tables):
    try:
        cur.execute(f"SELECT COUNT(*) as cnt FROM `{t}`")
        cnt = cur.fetchone()['cnt']
        print(f"Table: {t:25} -> {cnt:5} rows")
    except Exception as e:
        print(f"Table: {t:25} -> Error: {e}")

print("\n--- Detailed Columns for Key Business Tables ---")
for t in ['bikes', 'enquiries', 'users', 'admins', 'sold_bikes', 'bike_transactions', 'chat_conversations', 'chat_messages', 'notifications', 'favorites', 'contact_messages', 'admin_audit_logs']:
    if t in tables:
        print(f"\n[{t}] Columns:")
        cur.execute(f"DESCRIBE `{t}`")
        for col in cur.fetchall():
            print(f"  - {col['Field']:25} {col['Type']:20} Null:{col['Null']:4} Key:{col['Key']:4}")

cur.close()
conn.close()
