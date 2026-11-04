import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv('my-node-app/.env', override=True)

host = os.getenv('DB_HOST')
port = int(os.getenv('DB_PORT', 4000))
user = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')
database = os.getenv('DB_NAME')
ca = os.getenv('DB_SSL_CA')

print(f"Connecting to TiDB Cloud: {host}:{port}, db: {database}, user: {user[:5]}***")

cfg = {
    'host': host,
    'port': port,
    'user': user,
    'password': password,
    'database': database,
    'ssl_ca': ca,
    'ssl_verify_cert': True,
    'ssl_verify_identity': False,
    'connection_timeout': 10
}

try:
    conn = mysql.connector.connect(**cfg)
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT COUNT(*) as count FROM bikes")
    row = cur.fetchone()
    print("SUCCESS! TiDB Cloud returned bikes count:", row['count'])
    cur.execute("SELECT id, title, brand, model, price FROM bikes LIMIT 3")
    for b in cur.fetchall():
        print("  - Bike:", b)
    cur.close()
    conn.close()
except Exception as e:
    print("FAILED:", e)
