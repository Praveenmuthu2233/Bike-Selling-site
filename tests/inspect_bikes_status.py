import os
import sys
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '..', 'my-node-app', '.env')
load_dotenv(dotenv_path=env_path)

import mysql.connector

def inspect_bikes():
    host = os.getenv("DB_HOST", "gateway01.ap-southeast-1.prod.aws.tidbcloud.com")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    database = os.getenv("DB_NAME", "smr_motors")
    port = int(os.getenv("DB_PORT", 4000))

    conn = mysql.connector.connect(
        host=host, user=user, password=password, database=database, port=port,
        ssl_verify_cert=True, ssl_verify_identity=True
    )
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, title, status, listing_status, isSoldout FROM bikes")
    rows = cur.fetchall()
    print(f"Total rows in bikes: {len(rows)}")
    for r in rows:
        print(f"ID={r['id']} | status={r['status']} | listing_status={r['listing_status']} | isSoldout={r['isSoldout']} | {r['title']}")
    cur.close()
    conn.close()

if __name__ == "__main__":
    inspect_bikes()
