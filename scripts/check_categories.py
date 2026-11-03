import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'my-node-app')
import app
conn = app.get_db()
if conn:
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT COUNT(*) as c FROM categories")
    print("Categories count in TiDB:", cur.fetchone()['c'])
    cur.close()
    conn.close()
else:
    print("No DB connection")
