import os
import mysql.connector
from dotenv import dotenv_values

for env_file in ['.env', 'my-node-app/.env']:
    if os.path.exists(env_file):
        vals = dotenv_values(env_file)
        host = vals.get('DB_HOST') or vals.get('TIDB_HOST')
        port = int(vals.get('DB_PORT') or vals.get('TIDB_PORT') or 4000)
        user = vals.get('DB_USER') or vals.get('TIDB_USER')
        password = vals.get('DB_PASSWORD') or vals.get('TIDB_PASSWORD')
        database = vals.get('DB_NAME') or vals.get('TIDB_DATABASE') or 'smr_motors'
        
        print(f"Testing {env_file}: host={host}, user={user}, db={database}")
        try:
            conn = mysql.connector.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                ssl_ca='certs/isrgrootx1.pem',
                ssl_verify_cert=True,
                ssl_verify_identity=False,
                connection_timeout=5
            )
            print(f"  -> SUCCESS! Connected to {database}")
            cur = conn.cursor()
            cur.execute("SHOW TABLES")
            tables = [t[0] for t in cur.fetchall()]
            print(f"  -> Tables ({len(tables)}): {tables}")
            conn.close()
        except Exception as e:
            print(f"  -> FAILED: {e}")
