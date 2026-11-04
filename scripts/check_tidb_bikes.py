import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv('my-node-app/.env')

ssl_ca = os.getenv('TIDB_SSL_CA_PATH')
ssl_args = {'ca': ssl_ca} if ssl_ca and os.path.exists(ssl_ca) else None

conn = mysql.connector.connect(
    host=os.getenv('TIDB_HOST'),
    port=int(os.getenv('TIDB_PORT', 4000)),
    user=os.getenv('TIDB_USER'),
    password=os.getenv('TIDB_PASSWORD'),
    database=os.getenv('TIDB_DATABASE'),
    ssl_ca=ssl_ca if ssl_ca and os.path.exists(ssl_ca) else None,
    ssl_verify_cert=True if ssl_ca and os.path.exists(ssl_ca) else False
)

cursor = conn.cursor(dictionary=True)
cursor.execute("SELECT id, title, brand, model, price, status, isSoldout, created_at FROM bikes ORDER BY id DESC LIMIT 15")
rows = cursor.fetchall()
print(f"Total bikes returned in sample: {len(rows)}")
for r in rows:
    print(f"ID {r['id']}: {r['title']} | Brand: {r['brand']} | Price: {r['price']} | Status: {r['status']} | Sold: {r['isSoldout']}")

cursor.close()
conn.close()
