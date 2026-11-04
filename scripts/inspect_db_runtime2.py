import os
import sys
from dotenv import load_dotenv

app_dir = os.path.join(os.getcwd(), 'my-node-app')
local_env = os.path.join(app_dir, '.env')
root_env = os.path.join(os.getcwd(), '.env')

if os.path.exists(local_env):
    load_dotenv(local_env, override=True)
if os.path.exists(root_env):
    load_dotenv(root_env, override=False)
load_dotenv()

sys.path.insert(0, app_dir)
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
