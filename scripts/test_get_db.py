import sys
sys.path.insert(0, 'my-node-app')
import app

print("app.dbconfig:", {k: (v if k != 'password' else '***') for k, v in app.dbconfig.items()})
conn = app.get_db()
print("conn from app.get_db():", conn)
if conn:
    print("is_connected:", conn.is_connected())
    cur = conn.cursor()
    cur.execute("SELECT 1")
    print("SELECT 1 result:", cur.fetchone())
    cur.close()
    conn.close()
else:
    print("FAILED TO CONNECT!")
