import sys
sys.path.insert(0, 'my-node-app')
from dotenv import load_dotenv
load_dotenv('my-node-app/.env')

import db

print("--- Testing db.py Diagnostics ---")
diag = db.get_db_diagnostics()
print("Diagnostics:", diag)

print("\n--- Testing get_db() ---")
conn = db.get_db()
print("Connection object:", conn)
if conn:
    print("is_connected:", conn.is_connected())
    cur = conn.cursor()
    cur.execute("SELECT DATABASE(), 1+1")
    print("Query result:", cur.fetchone())
    cur.close()
    conn.close()

print("\n--- Testing get_db_cursor context manager ---")
with db.get_db_cursor(commit=False, dictionary=True) as (conn2, cursor2):
    cursor2.execute("SELECT COUNT(*) as bike_count FROM bikes")
    row = cursor2.fetchone()
    print("Bike count from context manager:", row)

print("\n--- Testing auto-reconnect on ping ---")
conn3 = db.get_db()
conn3.ping(reconnect=True)
print("Ping succeeded on conn3!")
conn3.close()

print("\nALL DB.PY TESTS PASSED!")
