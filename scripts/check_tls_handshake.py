import ssl
import socket

hostname = 'gateway01.ap-southeast-1.prod.aws.tidbcloud.com'
port = 4000

# TiDB requires MySQL protocol handshake before TLS starttls, but let's test mysql.connector verification directly
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv('my-node-app/.env')
ca_path = os.path.abspath('my-node-app/certs/isrgrootx1.pem')

try:
    c = mysql.connector.connect(
        host=hostname, port=port,
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME'),
        ssl_ca=ca_path,
        ssl_verify_cert=True,
        ssl_verify_identity=True
    )
    print("mysql.connector with ssl_verify_identity=True: CONNECTED!")
    print("TLS cipher in use:", c.get_server_info())
    c.close()
except Exception as e:
    print("Connection failed with ssl_verify_identity=True:", e)
