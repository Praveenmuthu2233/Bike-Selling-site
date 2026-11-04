import sys
sys.path.insert(0, 'my-node-app')
import db

print("DB_HOST:", db.DB_HOST)
print("DB_PORT:", db.DB_PORT)
print("DB_USER:", db.DB_USER)
print("DB_NAME:", db.DB_NAME)
print("PASSWORD length:", len(db.DB_PASSWORD))

conn = db.get_db()
if conn:
    print("SUCCESS! Connected via db.get_db()")
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT DATABASE() as db, VERSION() as ver")
    print(cur.fetchone())
    conn.close()
else:
    print("FAILED to connect via db.get_db()")
