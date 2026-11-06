import os
import sys
import json
import sqlite3
import datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 70)
print("TESTING MULTI-PRODUCT CHAT SWITCHING LOGIC (Product A, B, C)")
print("=" * 70)

# Create an in-memory SQLite database simulating TiDB Cloud
conn = sqlite3.connect(":memory:")
cursor = conn.cursor()

# Create schema
cursor.executescript("""
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    role TEXT DEFAULT 'user'
);

CREATE TABLE bikes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    brand TEXT NOT NULL,
    model TEXT NOT NULL,
    price REAL NOT NULL,
    images TEXT,
    status TEXT DEFAULT 'approved'
);

CREATE TABLE chat_conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    bike_id INTEGER,
    subject TEXT NOT NULL,
    status TEXT DEFAULT 'open',
    assigned_admin_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_message_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    sender_id INTEGER NOT NULL,
    sender_role TEXT NOT NULL,
    message TEXT NOT NULL,
    is_read INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

# Seed test data
cursor.execute("INSERT INTO users (name, email, role) VALUES ('Praveen Rider', 'praveen@example.com', 'user')")
user_id = cursor.lastrowid
cursor.execute("INSERT INTO users (name, email, role) VALUES ('SMR Admin', 'admin@smrmotors.in', 'superadmin')")
admin_id = cursor.lastrowid

# Seed 3 different products
cursor.execute("INSERT INTO bikes (title, brand, model, price, images) VALUES ('Royal Enfield Classic 350', 'Royal Enfield', 'Classic 350', 165000, '[\"/static/images/IMG-20251204-WA0053.jpg\"]')")
bike_a_id = cursor.lastrowid

cursor.execute("INSERT INTO bikes (title, brand, model, price, images) VALUES ('Yamaha YZF R15 V4', 'Yamaha', 'YZF R15 V4', 185000, '[\"/static/images/IMG-20251204-WA0054.jpg\"]')")
bike_b_id = cursor.lastrowid

cursor.execute("INSERT INTO bikes (title, brand, model, price, images) VALUES ('Honda Activa 6G', 'Honda', 'Activa 6G', 75000, '[\"/static/images/IMG-20251204-WA0055.jpg\"]')")
bike_c_id = cursor.lastrowid

# Create 3 distinct product chat conversations for user
now = datetime.datetime.now()
cursor.execute("INSERT INTO chat_conversations (user_id, bike_id, subject, status) VALUES (?, ?, ?, 'open')", 
               (user_id, bike_a_id, 'Inquiry about Royal Enfield Classic 350'))
conv_a_id = cursor.lastrowid

cursor.execute("INSERT INTO chat_conversations (user_id, bike_id, subject, status) VALUES (?, ?, ?, 'open')", 
               (user_id, bike_b_id, 'Inquiry about Yamaha YZF R15 V4'))
conv_b_id = cursor.lastrowid

cursor.execute("INSERT INTO chat_conversations (user_id, bike_id, subject, status) VALUES (?, ?, ?, 'open')", 
               (user_id, bike_c_id, 'Inquiry about Honda Activa 6G'))
conv_c_id = cursor.lastrowid

# Insert messages for each conversation
cursor.execute("INSERT INTO chat_messages (conversation_id, sender_id, sender_role, message) VALUES (?, ?, 'user', 'Is the Royal Enfield available for a test ride?')", (conv_a_id, user_id))
cursor.execute("INSERT INTO chat_messages (conversation_id, sender_id, sender_role, message) VALUES (?, ?, 'admin', 'Yes Praveen, Royal Enfield Classic 350 is available at Salem showroom.')", (conv_a_id, admin_id))

cursor.execute("INSERT INTO chat_messages (conversation_id, sender_id, sender_role, message) VALUES (?, ?, 'user', 'What is the best price for Yamaha R15?')", (conv_b_id, user_id))
cursor.execute("INSERT INTO chat_messages (conversation_id, sender_id, sender_role, message) VALUES (?, ?, 'admin', 'Yamaha R15 V4 is listed at ₹1,85,000 including inspection warranty.')", (conv_b_id, admin_id))

cursor.execute("INSERT INTO chat_messages (conversation_id, sender_id, sender_role, message) VALUES (?, ?, 'user', 'Single owner Activa 6G?')", (conv_c_id, user_id))
conn.commit()

# Simulate backend get conversations list
query = """
SELECT c.id, c.subject, c.status, c.created_at, c.last_message_at,
       c.bike_id, b.title AS bike_title, b.price AS bike_price, b.images AS bike_images,
       (SELECT m.message FROM chat_messages m WHERE m.conversation_id = c.id ORDER BY m.id DESC LIMIT 1) AS last_message
FROM chat_conversations c
LEFT JOIN bikes b ON b.id = c.bike_id
WHERE c.user_id = ?
ORDER BY c.last_message_at DESC
"""
cursor.execute(query, (user_id,))
rows = cursor.fetchall()
conversations = []
for r in rows:
    conversations.append({
        'id': r[0],
        'subject': r[1],
        'status': r[2],
        'bike_id': r[5],
        'bike_title': r[6],
        'bike_price': r[7],
        'last_message': r[9]
    })

print(f"Loaded {len(conversations)} distinct product conversations:")
for c in conversations:
    print(f"  - Conv #{c['id']}: [{c['bike_title']}] ₹{c['bike_price']:,} -> Last Msg: '{c['last_message']}'")

assert len(conversations) == 3, "Expected 3 conversations"
assert conversations[0]['bike_title'] in ['Royal Enfield Classic 350', 'Yamaha YZF R15 V4', 'Honda Activa 6G']

# Simulate Frontend Switching Test
def simulate_frontend_switch(active_conv_id):
    active_conv = next(c for c in conversations if c['id'] == active_conv_id)
    # Fetch messages for this conversation only
    cursor.execute("SELECT id, sender_role, message FROM chat_messages WHERE conversation_id = ? ORDER BY id ASC", (active_conv_id,))
    msgs = cursor.fetchall()
    print(f"\n[SWITCH TO CONV #{active_conv_id}] {active_conv['bike_title']} (₹{active_conv['bike_price']:,}):")
    print(f"  Header Title: {active_conv['bike_title']}")
    print(f"  Pinned Bike: {active_conv['bike_title']} (Price: ₹{active_conv['bike_price']:,})")
    print(f"  Messages Rendered ({len(msgs)} messages):")
    for m in msgs:
        print(f"    - [{m[1].upper()}]: {m[2]}")
    return msgs

# Test 1: Switch to Product A (Royal Enfield)
msgs_a = simulate_frontend_switch(conv_a_id)
assert any("Royal Enfield" in m[2] for m in msgs_a)
assert not any("Yamaha" in m[2] for m in msgs_a), "Message leak from Yamaha!"
assert not any("Activa" in m[2] for m in msgs_a), "Message leak from Activa!"

# Test 2: Switch to Product B (Yamaha R15)
msgs_b = simulate_frontend_switch(conv_b_id)
assert any("Yamaha" in m[2] for m in msgs_b)
assert not any("Royal Enfield" in m[2] for m in msgs_b), "Message leak from Royal Enfield!"
assert not any("Activa" in m[2] for m in msgs_b), "Message leak from Activa!"

# Test 3: Switch to Product C (Honda Activa)
msgs_c = simulate_frontend_switch(conv_c_id)
assert any("Activa" in m[2] for m in msgs_c)
assert not any("Royal Enfield" in m[2] for m in msgs_c)
assert not any("Yamaha" in m[2] for m in msgs_c)

print("\n" + "=" * 70)
print("MULTI-PRODUCT CHAT SWITCHING VERIFIED: 100% ISOLATED & ACCURATE!")
print("=" * 70)
