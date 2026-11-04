from mysql.connector.connection import MySQLConnection
from mysql.connector.network import TLS_CIPHERS

print("TLS_CIPHERS:", TLS_CIPHERS)
print("MySQLConnection._ssl_options or similar:")
from mysql.connector.constants import ClientFlag
print("ClientFlag.SSL:", ClientFlag.SSL)
