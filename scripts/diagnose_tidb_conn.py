import os
import sys
from dotenv import load_dotenv

load_dotenv('my-node-app/.env')
load_dotenv('.env')

host = os.getenv("DB_HOST") or os.getenv("TIDB_HOST")
port = int(os.getenv("DB_PORT") or os.getenv("TIDB_PORT") or 4000)
user = os.getenv("DB_USER") or os.getenv("TIDB_USER")
password = os.getenv("DB_PASSWORD") or os.getenv("TIDB_PASSWORD")
database = os.getenv("DB_NAME") or os.getenv("TIDB_DATABASE") or "smr_motors"
ssl_ca = os.getenv("DB_SSL_CA") or "my-node-app/certs/isrgrootx1.pem"

print(f"Host: {host}")
print(f"Port: {port}")
print(f"User: {user}")
print(f"Database: {database}")
print(f"Password repr: {repr(password)}")
print(f"SSL CA: {ssl_ca} (exists: {os.path.exists(ssl_ca)})")

# Test 1: mysql.connector with ssl_verify_cert=False
try:
    import mysql.connector
    print("\n--- Testing mysql.connector with ssl_disabled=False, ssl_verify_cert=False ---")
    conn = mysql.connector.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        ssl_ca=ssl_ca if os.path.exists(ssl_ca) else None,
        ssl_verify_cert=False,
        connection_timeout=10
    )
    print("mysql.connector SUCCESS!")
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    print("Query result:", cursor.fetchone())
    cursor.close()
    conn.close()
except Exception as e:
    print("mysql.connector failed:", type(e), e)

# Test 2: pymysql
try:
    import pymysql
    import ssl
    print("\n--- Testing pymysql with ssl context ---")
    ctx = ssl.create_default_context(cafile=ssl_ca if os.path.exists(ssl_ca) else None)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    conn2 = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        ssl=ctx,
        connect_timeout=10
    )
    print("pymysql SUCCESS!")
    cursor2 = conn2.cursor()
    cursor2.execute("SELECT 1")
    print("Query result:", cursor2.fetchone())
    cursor2.close()
    conn2.close()
except Exception as e:
    print("pymysql failed:", type(e), e)
