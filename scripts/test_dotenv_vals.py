import os
import mysql.connector
from dotenv import dotenv_values

vals = dotenv_values('my-node-app/.env')
print("Loaded keys from my-node-app/.env:")
for k, v in vals.items():
    if 'USER' in k or 'HOST' in k or 'PORT' in k or 'DATABASE' in k or 'NAME' in k:
        print(f"  {k} = {v}")
    elif 'PASSWORD' in k:
        print(f"  {k} = [length: {len(v)}]")

# Test direct connection using dotenv_values (unmangled)
cfg = {
    'host': vals['DB_HOST'],
    'port': int(vals['DB_PORT']),
    'user': vals['DB_USER'],
    'password': vals['DB_PASSWORD'],
    'database': vals['DB_NAME'],
    'ssl_ca': os.path.abspath('certs/isrgrootx1.pem'),
    'ssl_verify_cert': True,
    'ssl_verify_identity': False
}

print(f"Connecting to {cfg['host']}:{cfg['port']} with user {cfg['user']}...")
try:
    conn = mysql.connector.connect(**cfg)
    print("SUCCESS! Connected to TiDB!")
    cur = conn.cursor()
    cur.execute("SELECT 1")
    print("SELECT 1:", cur.fetchone())
    conn.close()
except Exception as e:
    print("FAILED:", type(e), e)
