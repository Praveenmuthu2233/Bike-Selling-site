import sys
import os

# Add my-node-app to path
sys.path.insert(0, os.path.join(os.getcwd(), "my-node-app"))

try:
    from app import app, get_db
    print("Flask app and get_db imported successfully")
    conn = get_db()
    if conn:
        print("Connected to database successfully!")
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT DATABASE() as db, VERSION() as ver")
        row = cursor.fetchone()
        print("Database Info:", row)
        cursor.close()
        conn.close()
    else:
        print("Could not connect to database (conn is None).")
except Exception as e:
    print("Error during db test:", str(e))
