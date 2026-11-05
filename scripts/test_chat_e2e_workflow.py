import os
import sys
import json
import sqlite3
import jwt
from datetime import datetime, timedelta

# Ensure UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'my-node-app'))

import app as flask_app
from app import app, JWT_SECRET

print("==================================================")
print("SMR MOTORS - END-TO-END CHAT & MESSAGING TEST")
print("==================================================")

# Setup SQLite in-memory database
db_conn = sqlite3.connect(":memory:", check_same_thread=False)
db_conn.row_factory = sqlite3.Row

cursor = db_conn.cursor()

# Create tables matching exact TiDB schema
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    google_id TEXT UNIQUE,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    profile_image TEXT,
    phone TEXT,
    role TEXT DEFAULT 'user',
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'superadmin',
    avatar TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS bikes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    brand TEXT NOT NULL,
    model TEXT NOT NULL,
    year INTEGER NOT NULL,
    price REAL NOT NULL,
    images TEXT,
    status TEXT DEFAULT 'approved'
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS bikesforsale (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    brand TEXT NOT NULL,
    model TEXT NOT NULL,
    year INTEGER NOT NULL,
    price REAL NOT NULL,
    images TEXT,
    status TEXT DEFAULT 'approved',
    listing_status TEXT DEFAULT 'approved'
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
CREATE TABLE IF NOT EXISTS chat_read_status (
    conversation_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    last_read_message_id INTEGER NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (conversation_id, user_id)
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

# Insert test users, admin, and bikes
cursor.execute("INSERT INTO users (id, name, email, profile_image) VALUES (101, 'Ramesh Kumar', 'ramesh@example.com', '/static/images/user101.jpg')")
cursor.execute("INSERT INTO users (id, name, email, profile_image) VALUES (202, 'Suresh Patel', 'suresh@example.com', '/static/images/user202.jpg')")
cursor.execute("INSERT INTO admins (id, username, email, password_hash, role) VALUES (1, 'admin_master', 'admin@smrmotors.com', 'hashed_pw', 'superadmin')")
cursor.execute("""
    INSERT INTO bikes (id, title, brand, model, year, price, images)
    VALUES (55, 'Royal Enfield Classic 350', 'Royal Enfield', 'Classic 350', 2022, 175000, '[\"/static/images/bike.jpg\"]')
""")
cursor.execute("""
    INSERT INTO bikesforsale (id, title, brand, model, year, price, images)
    VALUES (55, 'Royal Enfield Classic 350', 'Royal Enfield', 'Classic 350', 2022, 175000, '[\"/static/images/bike.jpg\"]')
""")
db_conn.commit()

class MySQLCursorAdapter:
    def __init__(self, sqlite_cursor):
        self._cur = sqlite_cursor

    def execute(self, sql, params=None):
        clean_sql = sql.replace("%s", "?")
        
        # Handle MySQL ON DUPLICATE KEY UPDATE in SQLite
        if "ON DUPLICATE KEY UPDATE" in clean_sql:
            if "chat_read_status" in clean_sql:
                clean_sql = "INSERT INTO chat_read_status (conversation_id, user_id, last_read_message_id) VALUES (?, ?, ?) ON CONFLICT(conversation_id, user_id) DO UPDATE SET last_read_message_id = excluded.last_read_message_id"
                if params and len(params) == 4:
                    params = (params[0], params[1], max(params[2], params[3]))

        # Handle MySQL GREATEST
        if "GREATEST(" in clean_sql:
            clean_sql = clean_sql.replace("GREATEST(", "MAX(")

        if params is None:
            return self._cur.execute(clean_sql)
        else:
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

    def close(self):
        pass

class MySQLConnAdapter:
    def __init__(self, conn):
        self._conn = conn

    def cursor(self, dictionary=True):
        return MySQLCursorAdapter(self._conn.cursor())

    def commit(self):
        self._conn.commit()

    def close(self):
        pass

# Wire adapter to Flask app
flask_app.get_db = lambda: MySQLConnAdapter(db_conn)

client = app.test_client()

# Generate JWT tokens
def create_user_token(user_id=101, email="ramesh@example.com", name="Ramesh Kumar", role="user"):
    payload = {
        'id': user_id,
        'user_id': user_id,
        'email': email,
        'name': name,
        'username': 'ramesh',
        'role': role,
        'exp': datetime.utcnow() + timedelta(days=1)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def create_admin_token(admin_id=1, username="admin_master", role="superadmin"):
    payload = {
        'id': admin_id,
        'admin_id': admin_id,
        'username': username,
        'role': role,
        'exp': datetime.utcnow() + timedelta(days=1)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

user1_token = create_user_token(user_id=101, email="ramesh@example.com", name="Ramesh Kumar")
user2_token = create_user_token(user_id=202, email="suresh@example.com", name="Suresh Patel")
admin_token = create_admin_token(admin_id=1, username="admin_master", role="superadmin")

passed_checks = 0
total_checks = 0

def check(name, condition, details=""):
    global passed_checks, total_checks
    total_checks += 1
    if condition:
        passed_checks += 1
        print(f"[PASS] {name}")
    else:
        print(f"[FAIL] {name} - Details: {details}")

# 1. User starts a new chat inquiry
print("\n--- Test 1: User creates new inquiry with bike attachment ---")
res = client.post('/api/chat/conversations', 
    headers={'Authorization': f'Bearer {user1_token}'},
    json={
        'subject': 'Inquiry about Royal Enfield Classic 350',
        'bike_id': 55,
        'message': 'Hello SMR Team, is this Classic 350 available for test drive this Saturday?'
    }
)
data = res.get_json()
check("User created chat conversation successfully (status 201)", res.status_code == 201, data)
check("Conversation response contains conversation_id", 'conversation_id' in data and data.get('conversation_id') is not None, data)

conv_id = data.get('conversation_id')

# 2. Prevent rapid duplicate conversation submission
print("\n--- Test 2: Prevent rapid duplicate conversation ---")
res_dup = client.post('/api/chat/conversations', 
    headers={'Authorization': f'Bearer {user1_token}'},
    json={
        'subject': 'Inquiry about Royal Enfield Classic 350',
        'bike_id': 55,
        'message': 'Hello SMR Team, is this Classic 350 available for test drive this Saturday?'
    }
)
dup_data = res_dup.get_json()
check("Backend prevents duplicate conversation on rapid retry", res_dup.status_code in (200, 201) and dup_data.get('conversation_id') == conv_id and dup_data.get('reused_existing') is True, dup_data)

# 3. User lists their conversations
print("\n--- Test 3: User lists conversations ---")
res_list = client.get('/api/chat/conversations', headers={'Authorization': f'Bearer {user1_token}'})
list_data = res_list.get_json()
check("User receives conversation list (status 200)", res_list.status_code == 200, list_data)
user_convs = list_data.get('conversations', [])
check("Created conversation is present in user list", any(c['id'] == conv_id for c in user_convs), user_convs)
if user_convs:
    c0 = user_convs[0]
    check("Conversation includes attached bike title", 'Classic 350' in (c0.get('bike_title') or ''), c0)
    check("Last message preview matches initial message", 'test drive this Saturday' in (c0.get('last_message') or ''), c0)

# 4. User views messages in the conversation
print("\n--- Test 4: User retrieves conversation messages ---")
res_msgs = client.get(f'/api/chat/conversations/{conv_id}/messages', headers={'Authorization': f'Bearer {user1_token}'})
msgs_data = res_msgs.get_json()
check("User receives messages stream (status 200)", res_msgs.status_code == 200, msgs_data)
msgs = msgs_data.get('messages', [])
check("Initial message is present in message stream", len(msgs) >= 1, msgs)
check("Message sender_role is 'user'", msgs[0]['sender_role'] == 'user', msgs[0] if msgs else None)
first_msg_id = msgs[0]['id'] if msgs else 0

# 5. Admin lists conversations
print("\n--- Test 5: Admin retrieves customer conversations ---")
res_admin_convs = client.get('/api/admin/chat/conversations', headers={'Authorization': f'Bearer {admin_token}'})
admin_convs_data = res_admin_convs.get_json()
check("Admin fetches conversations (status 200)", res_admin_convs.status_code == 200, admin_convs_data)
admin_convs = admin_convs_data.get('conversations', [])
matched_conv = next((c for c in admin_convs if c['id'] == conv_id), None)
check("Conversation appears in Admin Panel", matched_conv is not None, admin_convs)
if matched_conv:
    check("Admin sees customer name 'Ramesh Kumar'", matched_conv['customer']['name'] == 'Ramesh Kumar', matched_conv)
    check("Admin sees customer email 'ramesh@example.com'", matched_conv['customer']['email'] == 'ramesh@example.com', matched_conv)
    check("Admin sees unread count >= 1 for customer message", matched_conv['unread_count'] >= 1, matched_conv)

# 6. Admin reads conversation messages and replies
print("\n--- Test 6: Admin opens messages and sends reply ---")
res_admin_msgs = client.get(f'/api/admin/chat/conversations/{conv_id}/messages', headers={'Authorization': f'Bearer {admin_token}'})
check("Admin opens conversation messages (status 200)", res_admin_msgs.status_code == 200)

res_reply = client.post(f'/api/admin/chat/conversations/{conv_id}/messages',
    headers={'Authorization': f'Bearer {admin_token}'},
    json={'message': 'Yes Ramesh! The Classic 350 is available for inspection and test ride at Salem showroom.'}
)
reply_data = res_reply.get_json()
check("Admin sends reply message successfully (status 201)", res_reply.status_code == 201, reply_data)
admin_msg_id = reply_data.get('message', {}).get('id')
check("Reply returns new message ID", admin_msg_id is not None, reply_data)

# 7. User polls for new messages via delta polling (since_id)
print("\n--- Test 7: User delta polling receives admin reply ---")
res_poll = client.get(f'/api/chat/conversations/{conv_id}/messages?since_id={first_msg_id}', headers={'Authorization': f'Bearer {user1_token}'})
poll_data = res_poll.get_json()
check("User poll returns status 200", res_poll.status_code == 200, poll_data)
new_msgs = poll_data.get('messages', [])
check("User delta poll receives only the new admin reply", any(m['id'] == admin_msg_id for m in new_msgs), new_msgs)
admin_received_msg = next((m for m in new_msgs if m['id'] == admin_msg_id), None)
if admin_received_msg:
    check("Sender role is admin", admin_received_msg['sender_role'] in ('admin', 'superadmin'), admin_received_msg)
    check("Message content matches admin text", 'Salem showroom' in admin_received_msg['message'], admin_received_msg)

# 8. User sends follow-up message
print("\n--- Test 8: User sends follow-up response ---")
res_user_msg2 = client.post(f'/api/chat/conversations/{conv_id}/messages',
    headers={'Authorization': f'Bearer {user1_token}'},
    json={'message': 'Great, I will visit around 11 AM. Thank you!'}
)
check("User sends follow-up successfully (status 201)", res_user_msg2.status_code == 201, res_user_msg2.get_json())
user_msg2_id = res_user_msg2.get_json().get('message', {}).get('id')

# 9. Admin receives user follow-up via delta polling
print("\n--- Test 9: Admin receives follow-up via delta polling ---")
res_admin_poll = client.get(f'/api/admin/chat/conversations/{conv_id}/messages?since_id={admin_msg_id}', headers={'Authorization': f'Bearer {admin_token}'})
admin_poll_data = res_admin_poll.get_json()
check("Admin delta poll returns status 200", res_admin_poll.status_code == 200, admin_poll_data)
admin_new_msgs = admin_poll_data.get('messages', [])
check("Admin poll receives user follow-up message", any(m['id'] == user_msg2_id for m in admin_new_msgs), admin_new_msgs)

# 10. Security: Cross-user isolation check
print("\n--- Test 10: Security check - unauthorized user cannot access conversation ---")
res_unauth = client.get(f'/api/chat/conversations/{conv_id}/messages', headers={'Authorization': f'Bearer {user2_token}'})
check("Unauthorized user 202 is blocked from user 101's chat (status 403)", res_unauth.status_code == 403, res_unauth.get_json())

res_unauth_send = client.post(f'/api/chat/conversations/{conv_id}/messages',
    headers={'Authorization': f'Bearer {user2_token}'},
    json={'message': 'Malicious attempt to inject message into someone elses chat'}
)
check("Unauthorized user 202 blocked from posting into user 101's chat (status 403)", res_unauth_send.status_code == 403, res_unauth_send.get_json())

# 11. Admin resolves conversation
print("\n--- Test 11: Admin marks conversation as resolved ---")
res_status = client.put(f'/api/admin/chat/conversations/{conv_id}/status',
    headers={'Authorization': f'Bearer {admin_token}'},
    json={'status': 'resolved'}
)
check("Admin marks conversation as resolved (status 200)", res_status.status_code == 200, res_status.get_json())

# User verifies conversation status is now resolved
res_check_status = client.get(f'/api/chat/conversations/{conv_id}/messages', headers={'Authorization': f'Bearer {user1_token}'})
check("Conversation status updated to 'resolved'", res_check_status.get_json().get('conversation', {}).get('status') == 'resolved')

# 12. Unread count endpoint
print("\n--- Test 12: Unread count endpoint ---")
res_unread = client.get('/api/chat/unread-count', headers={'Authorization': f'Bearer {user1_token}'})
check("User unread count endpoint returns 200", res_unread.status_code == 200, res_unread.get_json())

print("\n==================================================")
print(f"FINAL TEST RESULTS: {passed_checks}/{total_checks} checks passed!")
print("==================================================")

if passed_checks == total_checks:
    print("ALL TESTS PASSED SUCCESSFULLY! User chat end-to-end functionality is fully verified and operational.")
    sys.exit(0)
else:
    print("SOME TESTS FAILED! Review output above.")
    sys.exit(1)
