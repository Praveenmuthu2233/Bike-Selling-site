import os
import sys
import json
from dotenv import load_dotenv

load_dotenv('my-node-app/.env')
load_dotenv('.env')

sys.path.insert(0, 'my-node-app')
import db

def delete_admin_account_1():
    print("Checking connection to TiDB Cloud...")
    conn = db.get_db()
    if not conn:
        print("[ERROR] Cannot connect to TiDB Cloud to delete account.")
        return False

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM admins WHERE id = 1 AND username = 'admin'")
        row = cursor.fetchone()
        if not row:
            print("[INFO] Account ID 1 ('admin') does not exist or was already deleted.")
            cursor.close()
            conn.close()
            return True

        print("[FOUND] Admin account ID 1:", row)

        # Reassign any conversations or foreign keys if necessary
        cursor.execute("UPDATE chat_conversations SET assigned_admin_id = NULL WHERE assigned_admin_id = 1")
        
        # Delete admin 1
        cursor.execute("DELETE FROM admins WHERE id = 1")
        conn.commit()
        print("[SUCCESS] Account ID 1 ('admin') has been permanently removed from TiDB Cloud admins table.")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print("[ERROR] Deletion failed:", e)
        if conn:
            try: conn.close()
            except Exception: pass
        return False

if __name__ == '__main__':
    delete_admin_account_1()
