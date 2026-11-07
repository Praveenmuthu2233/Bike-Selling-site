import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), "my-node-app"))
from app import get_db

conn = get_db()
if conn:
    c = conn.cursor(dictionary=True)
    c.execute("SHOW TABLES")
    tables = [list(r.values())[0] for r in c.fetchall()]
    print("Tables:", tables)
    for t in ["bikes", "sold_bikes", "bike_transactions", "buyer_details"]:
        if t in tables:
            c.execute(f"SELECT COUNT(*) as cnt FROM {t}")
            print(f"{t} count:", c.fetchone()["cnt"])
    c.execute("SELECT COUNT(*) as cnt FROM bikes WHERE isSoldout=1 OR status IN ('sold','soldout') OR listing_status IN ('sold','soldout')")
    print("sold bikes in bikes table:", c.fetchone()["cnt"])
    c.close()
    conn.close()
else:
    print("No DB connection (sandbox network restrictions)")
