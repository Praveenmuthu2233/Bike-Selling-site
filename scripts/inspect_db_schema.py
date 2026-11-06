import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath('my-node-app'))

def inspect_db():
    import app
    conn = app.get_db()
    if not conn:
        print("[Notice] Could not connect to TiDB directly from local environment.")
        return False
    
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SHOW TABLES")
        tables = cur.fetchall()
        print("=== TiDB Cloud Tables ===")
        for t in tables:
            print(list(t.values())[0])

        print("\n=== chat_conversations Schema ===")
        cur.execute("DESCRIBE chat_conversations")
        for col in cur.fetchall():
            print(col)

        print("\n=== chat_messages Schema ===")
        cur.execute("DESCRIBE chat_messages")
        for col in cur.fetchall():
            print(col)

        cur.close()
        conn.close()
        return True
    except Exception as e:
        print("Database error:", e)
        if conn:
            try: conn.close()
            except: pass
        return False

if __name__ == '__main__':
    inspect_db()
