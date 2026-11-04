import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv('my-node-app/.env')

host = os.getenv('DB_HOST') or os.getenv('TIDB_HOST')
port = int(os.getenv('DB_PORT') or os.getenv('TIDB_PORT') or 4000)
user = os.getenv('DB_USER') or os.getenv('TIDB_USER')
password = os.getenv('DB_PASSWORD') or os.getenv('TIDB_PASSWORD')
database = os.getenv('DB_NAME') or os.getenv('TIDB_DATABASE') or 'smr_motors'

print(f"Testing TiDB with host={host}, user={user[:4]}***, port={port}, db={database}")

# Test 1: with ssl_verify_identity=True and ssl_ca
ca_path = os.path.abspath('my-node-app/certs/isrgrootx1.pem')
print(f"CA exists: {os.path.exists(ca_path)}")

try:
    c1 = mysql.connector.connect(
        host=host, port=port, user=user, password=password, database=database,
        ssl_ca=ca_path, ssl_verify_cert=True, ssl_verify_identity=True
    )
    print("Test 1 (ssl_verify_identity=True): SUCCESS!", c1.is_connected())
    c1.close()
except Exception as e:
    print("Test 1 FAILED:", e)

# Test 2: without ssl_verify_identity (only ssl_verify_cert=True)
try:
    c2 = mysql.connector.connect(
        host=host, port=port, user=user, password=password, database=database,
        ssl_ca=ca_path, ssl_verify_cert=True
    )
    print("Test 2 (ssl_verify_cert=True): SUCCESS!", c2.is_connected())
    c2.close()
except Exception as e:
    print("Test 2 FAILED:", e)

# Test 3: without ssl_ca (relying on system/default TLS)
try:
    c3 = mysql.connector.connect(
        host=host, port=port, user=user, password=password, database=database,
        ssl_disabled=False
    )
    print("Test 3 (ssl_disabled=False, no ca file): SUCCESS!", c3.is_connected())
    c3.close()
except Exception as e:
    print("Test 3 FAILED:", e)

# Test 4: MySQLConnectionPool
try:
    from mysql.connector import pooling
    pool = pooling.MySQLConnectionPool(
        pool_name="test_p", pool_size=3,
        host=host, port=port, user=user, password=password, database=database,
        ssl_ca=ca_path, ssl_verify_cert=True
    )
    cp = pool.get_connection()
    print("Test 4 (MySQLConnectionPool): SUCCESS!", cp.is_connected())
    cp.close()
except Exception as e:
    print("Test 4 FAILED:", e)
