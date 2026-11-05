import os
import sys
import json
import sqlite3
import jwt
from datetime import datetime, timedelta

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'my-node-app'))

import app as flask_app
from app import app, JWT_SECRET

print("==================================================")
print("TESTING ADMIN CHAT: FILTERS, SEARCH, EMPTY STATES")
print("==================================================")

db_conn = sqlite3.connect(":memory:", check_same_thread=False)
db_conn.row_factory = sqlite3.Row
cursor = db_conn.cursor()

# Tables
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    profile_image TEXT,
    role TEXT DEFAULT 'user'
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    role TEXT DEFAULT 'superadmin'
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS bikes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    brand TEXT NOT NULL,
    model TEXT NOT NULL,
    price REAL NOT NULL,
    images TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS bikesforsale (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    brand TEXT NOT NULL,
    model TEXT NOT NULL,
    price REAL NOT NULL,
    images TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS chat_conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    bike_id INTEGER,
    subject TEXT NOT NULL,
    status TEXT DEFAULT 'open',
    assigned_admin_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    sender_id INTEGER NOT NULL,
    sender_role TEXT NOT NULL,
    message TEXT NOT NULL,
    is_read INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    target_role TEXT DEFAULT 'user',
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    type TEXT DEFAULT 'info',
    link TEXT,
    is_read INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# Seed users
cursor.execute("INSERT INTO users (id, name, email) VALUES (1, 'Karthik Raja', 'karthik@example.com')")
cursor.execute("INSERT INTO users (id, name, email) VALUES (2, 'Ananya Sharma', 'ananya@example.com')")
cursor.execute("INSERT INTO users (id, name, email) VALUES (3, 'Vikram Seth', 'vikram@example.com')")
cursor.execute("INSERT INTO admins (id, username, role) VALUES (1, 'admin', 'superadmin')")

# Seed bikes
cursor.execute("INSERT INTO bikes (id, title, brand, model, price, images) VALUES (10, 'Yamaha R15 V4', 'Yamaha', 'R15', 185000, '[]')")
cursor.execute("INSERT INTO bikesforsale (id, title, brand, model, price, images) VALUES (20, 'KTM Duke 390', 'KTM', 'Duke 390', 295000, '[]')")

# Conversation 1: Karthik - Open, Unread (bike 10)
cursor.execute("INSERT INTO chat_conversations (id, user_id, bike_id, subject, status) VALUES (1, 1, 10, 'Yamaha R15 Test Ride', 'open')")
cursor.execute("INSERT INTO chat_messages (conversation_id, sender_id, sender_role, message, is_read) VALUES (1, 1, 'user', 'Is Yamaha R15 available today?', 0)")

# Conversation 2: Ananya - Resolved, Read (bike 20)
cursor.execute("INSERT INTO chat_conversations (id, user_id, bike_id, subject, status) VALUES (2, 2, 20, 'KTM Duke Price Inquiry', 'resolved')")
cursor.execute("INSERT INTO chat_messages (conversation_id, sender_id, sender_role, message, is_read) VALUES (2, 2, 'user', 'Can you discount the KTM?', 1)")
cursor.execute("INSERT INTO chat_messages (conversation_id, sender_id, sender_role, message, is_read) VALUES (2, 1, 'admin', 'Best price is 2.9 Lakhs.', 1)")

# Conversation 3: Vikram - Open, Read (General support, no bike)
cursor.execute("INSERT INTO chat_conversations (id, user_id, bike_id, subject, status) VALUES (3, 3, NULL, 'Financing query', 'open')")
cursor.execute("INSERT INTO chat_messages (conversation_id, sender_id, sender_role, message, is_read) VALUES (3, 3, 'user', 'Do you offer HDFC finance?', 1)")

db_conn.commit()

class SimpleAdapter:
    def __init__(self, c):
        self._cur = c
    def execute(self, sql, params=None):
        clean_sql = sql.replace("%s", "?")
        if params is None:
            return self._cur.execute(clean_sql)
        return self._cur.execute(clean_sql, tuple(params))
    def fetchone(self):
        r = self._cur.fetchone()
        return dict(r) if r else None
    def fetchall(self):
        rows = self._cur.fetchall()
        return [dict(r) for r in rows] if rows else []
    @property
    def lastrowid(self):
        return self._cur.lastrowid
    def close(self): pass

class ConnAdapter:
    def __init__(self, conn):
        self._conn = conn
    def cursor(self, dictionary=True):
        return SimpleAdapter(self._conn.cursor())
    def commit(self): self._conn.commit()
    def close(self): pass

flask_app.get_db = lambda: ConnAdapter(db_conn)
client = app.test_client()

admin_payload = {'id': 1, 'admin_id': 1, 'username': 'admin', 'role': 'superadmin', 'exp': datetime.utcnow() + timedelta(days=1)}
admin_token = jwt.encode(admin_payload, JWT_SECRET, algorithm='HS256')
headers = {'Authorization': f'Bearer {admin_token}'}

# Test A: Filter 'all'
res_all = client.get('/api/admin/chat/conversations?filter=all', headers=headers)
assert res_all.status_code == 200
convs_all = res_all.get_json()['conversations']
assert len(convs_all) == 3
print("[PASS] Filter 'all' returned all 3 conversations")

# Test B: Filter 'unread'
res_unread = client.get('/api/admin/chat/conversations?filter=unread', headers=headers)
assert res_unread.status_code == 200
convs_unread = res_unread.get_json()['conversations']
assert len(convs_unread) == 1
assert convs_unread[0]['id'] == 1
print("[PASS] Filter 'unread' returned only conversation #1 (Karthik Raja with unread message)")

# Test C: Filter 'open'
res_open = client.get('/api/admin/chat/conversations?filter=open', headers=headers)
assert res_open.status_code == 200
convs_open = res_open.get_json()['conversations']
assert len(convs_open) == 2
assert set(c['id'] for c in convs_open) == {1, 3}
print("[PASS] Filter 'open' returned 2 open conversations (#1 and #3)")

# Test D: Filter 'resolved'
res_res = client.get('/api/admin/chat/conversations?filter=resolved', headers=headers)
assert res_res.status_code == 200
convs_res = res_res.get_json()['conversations']
assert len(convs_res) == 1
assert convs_res[0]['id'] == 2
print("[PASS] Filter 'resolved' returned only conversation #2 (Ananya Sharma)")

# Test E: Search by customer name
res_search_name = client.get('/api/admin/chat/conversations?filter=all&search=karthik', headers=headers)
convs_search_name = res_search_name.get_json()['conversations']
assert len(convs_search_name) == 1 and convs_search_name[0]['customer']['name'] == 'Karthik Raja'
print("[PASS] Search by name 'karthik' matched conversation #1")

# Test F: Search by customer email
res_search_email = client.get('/api/admin/chat/conversations?filter=all&search=ananya@example.com', headers=headers)
convs_search_email = res_search_email.get_json()['conversations']
assert len(convs_search_email) == 1 and convs_search_email[0]['customer']['name'] == 'Ananya Sharma'
print("[PASS] Search by email 'ananya@example.com' matched conversation #2")

# Test G: Search by bike title
res_search_bike = client.get('/api/admin/chat/conversations?filter=all&search=duke', headers=headers)
convs_search_bike = res_search_bike.get_json()['conversations']
assert len(convs_search_bike) == 1 and convs_search_bike[0]['bike']['title'] == 'KTM Duke 390'
print("[PASS] Search by bike 'duke' matched conversation with KTM Duke 390")

# Test H: Search with zero matches
res_zero = client.get('/api/admin/chat/conversations?filter=all&search=nonexistent', headers=headers)
assert len(res_zero.get_json()['conversations']) == 0
print("[PASS] Search with zero matches returned empty array (status 200)")

print("\n==================================================")
print("ALL ADMIN CHAT FILTER & SEARCH TESTS PASSED!")
print("==================================================")
