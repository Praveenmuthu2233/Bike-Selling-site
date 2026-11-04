import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'my-node-app')
import app

conn = app.get_db()
if not conn:
    print("Failed to get DB connection from app.get_db()!")
    sys.exit(1)

cur = conn.cursor(dictionary=True)
cur.execute("SELECT id, title, brand, model, price, status, isSoldout, created_at FROM bikes ORDER BY id DESC LIMIT 10")
rows = cur.fetchall()
print(f"Sample 10 bikes from TiDB Cloud:")
for r in rows:
    print(f"ID {r['id']}: {r['title']} | Rs.{r['price']} | Status: {r['status']} | Sold: {r['isSoldout']}")

cur.execute("SELECT COUNT(*) as c FROM bikes WHERE status='approved' AND isSoldout=0")
active_cnt = cur.fetchone()['c']
print(f"Total Active Approved Bikes in TiDB Cloud: {active_cnt}")

cur.close()
conn.close()
