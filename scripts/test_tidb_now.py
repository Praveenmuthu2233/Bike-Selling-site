import mysql.connector
from dotenv import dotenv_values

vals = dotenv_values('my-node-app/.env')
print("Testing TiDB connection...")
cfg = {
    'host': vals['DB_HOST'],
    'port': int(vals['DB_PORT']),
    'user': vals['DB_USER'],
    'password': vals['DB_PASSWORD'],
    'database': vals['DB_NAME'],
    'ssl_ca': 'certs/isrgrootx1.pem',
    'ssl_verify_cert': True,
    'ssl_verify_identity': False,
    'connection_timeout': 10
}

try:
    conn = mysql.connector.connect(**cfg)
    print("SUCCESS: Connected to TiDB!")
    conn.close()
except Exception as e:
    print("FAILED:", e)
