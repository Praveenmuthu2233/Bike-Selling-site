from mysql.connector import pooling

try:
    p1 = pooling.MySQLConnectionPool(pool_name="test_pool", pool_size=1)
except Exception as e:
    print("Pool 1 error (expected if no host, but let's check name clash):", e)
