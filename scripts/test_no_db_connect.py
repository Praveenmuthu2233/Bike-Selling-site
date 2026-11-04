import sys
sys.path.insert(0, 'my-node-app')
from dotenv import load_dotenv
load_dotenv('my-node-app/.env')
import mysql.connector
import db

cfg = dict(db.db_config)
db_name = cfg.pop("database")

print("Testing connect without database parameter...")
try:
    c = mysql.connector.connect(**cfg)
    print("Connected without database parameter! is_connected:", c.is_connected())
    cur = c.cursor()
    cur.execute("SELECT 1")
    print("SELECT 1:", cur.fetchone())
    cur.close()
    c.close()
except Exception as e:
    print("Failed to connect without database:", e)
