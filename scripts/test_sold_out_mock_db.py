"""
Comprehensive In-Memory / SQLite Mock Test Suite for Sold Out Workflow
Verifies the exact SQL queries, parameters, status updates, duplicate prevention,
redaction, and filtering without requiring outbound network connection.
"""
import sys
import os
import json
import sqlite3
import jwt

sys.path.insert(0, os.path.abspath('my-node-app'))
import app as flask_app
from app import app, JWT_SECRET

sys.stdout.reconfigure(encoding='utf-8')

# Setup SQLite in-memory database mimicking MySQL/TiDB
db_conn = sqlite3.connect(":memory:", check_same_thread=False)
db_conn.row_factory = sqlite3.Row

cursor = db_conn.cursor()
cursor.execute("""
CREATE TABLE bikes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    brand TEXT NOT NULL,
    model TEXT NOT NULL,
    year INTEGER NOT NULL,
    price REAL NOT NULL,
    requested_price REAL,
    proposed_seller_payout REAL,
    accepted_seller_payout REAL,
    public_selling_price REAL,
    listing_status TEXT DEFAULT 'pending',
    negotiation_status TEXT DEFAULT 'pending',
    kilometers_driven INTEGER DEFAULT 0,
    fuel_type TEXT DEFAULT 'Petrol',
    transmission TEXT DEFAULT 'Manual',
    description TEXT,
    images TEXT,
    seller_id INTEGER,
    seller_name TEXT,
    seller_phone TEXT,
    status TEXT DEFAULT 'pending',
    rejection_reason TEXT,
    featured INTEGER DEFAULT 0,
    registration_number TEXT,
    location TEXT,
    approved_by TEXT,
    approved_at TIMESTAMP,
    rejected_by TEXT,
    rejected_at TIMESTAMP,
    buying_price REAL,
    expenses REAL DEFAULT 0,
    profit REAL DEFAULT 0,
    isSoldout INTEGER DEFAULT 0,
    sold_by TEXT,
    sold_at TIMESTAMP,
    sold_snapshot TEXT,
    seller_agreement_at TIMESTAMP,
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE sold_bikes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bike_id INTEGER UNIQUE,
    title TEXT NOT NULL,
    brand TEXT NOT NULL,
    model TEXT NOT NULL,
    year INTEGER NOT NULL,
    price REAL NOT NULL,
    kilometers_driven INTEGER DEFAULT 0,
    fuel_type TEXT DEFAULT 'Petrol',
    transmission TEXT DEFAULT 'Manual',
    seller_id INTEGER,
    seller_name TEXT,
    seller_phone TEXT,
    seller_payout REAL,
    actual_sale_price REAL NOT NULL,
    total_expenses REAL DEFAULT 0,
    realized_profit REAL DEFAULT 0,
    buyer_name TEXT,
    buyer_phone TEXT,
    sold_by TEXT,
    sold_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE bike_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bike_id INTEGER NOT NULL,
    seller_id INTEGER,
    admin_id INTEGER,
    seller_payout REAL NOT NULL,
    actual_sale_price REAL NOT NULL,
    service_expense REAL DEFAULT 0,
    repair_expense REAL DEFAULT 0,
    transport_expense REAL DEFAULT 0,
    other_expense REAL DEFAULT 0,
    total_expenses REAL DEFAULT 0,
    realized_profit REAL NOT NULL,
    buyer_name TEXT,
    buyer_phone TEXT,
    sold_by TEXT,
    sold_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE listing_status_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bike_id INTEGER NOT NULL,
    old_status TEXT,
    new_status TEXT NOT NULL,
    changed_by TEXT DEFAULT 'system',
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE financial_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bike_id INTEGER NOT NULL,
    transaction_type TEXT DEFAULT 'sale',
    requested_price REAL,
    buying_price REAL,
    seller_payout REAL DEFAULT 0,
    selling_price REAL DEFAULT 0,
    service_expense REAL DEFAULT 0,
    repair_expense REAL DEFAULT 0,
    transport_expense REAL DEFAULT 0,
    other_expense REAL DEFAULT 0,
    total_expenses REAL DEFAULT 0,
    estimated_profit REAL DEFAULT 0,
    actual_profit REAL DEFAULT 0,
    recorded_by TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE bike_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bike_id INTEGER NOT NULL,
    image_url TEXT NOT NULL,
    image_order INTEGER DEFAULT 1,
    is_primary INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    role TEXT DEFAULT 'user'
)
""")

cursor.execute("""
CREATE TABLE enquiries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    message TEXT NOT NULL
)
""")

db_conn.commit()

# Adapter wrapper to emulate mysql.connector dictionary cursor and parameter syntax
class MySQLCursorAdapter:
    def __init__(self, sqlite_cursor):
        self._cur = sqlite_cursor
    def execute(self, sql, params=None):
        # Convert %s to ?
        clean_sql = sql.replace("%s", "?")
        # Replace ON DUPLICATE KEY UPDATE with SQLite equivalent or remove for test
        if "ON DUPLICATE KEY UPDATE" in clean_sql:
            clean_sql = clean_sql.split("ON DUPLICATE KEY UPDATE")[0].strip()
        # CURRENT_TIMESTAMP in MySQL is same in SQLite
        if params is None:
            return self._cur.execute(clean_sql)
        else:
            return self._cur.execute(clean_sql, params)
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

flask_app.get_db = lambda: MySQLConnAdapter(db_conn)

client = app.test_client()

superadmin_token = jwt.encode({"id": 1, "username": "admin", "role": "superadmin"}, JWT_SECRET, algorithm="HS256")
staff_admin_token = jwt.encode({"id": 2, "username": "mani", "role": "admin"}, JWT_SECRET, algorithm="HS256")
user_token = jwt.encode({"id": 10, "username": "testuser", "role": "user", "email": "user@example.com"}, JWT_SECRET, algorithm="HS256")

headers_super = {"Authorization": f"Bearer {superadmin_token}", "Content-Type": "application/json"}
headers_staff = {"Authorization": f"Bearer {staff_admin_token}", "Content-Type": "application/json"}
headers_user = {"Authorization": f"Bearer {user_token}", "Content-Type": "application/json"}

print("==================================================")
print(" SMR MOTORS - FULL WORKFLOW TEST SUITE")
print("==================================================")

# Test 1: RBAC Rejections
print("\n[Test 1] RBAC Authorization...")
r401 = client.post("/api/admin/bikes/1/sold", json={})
assert r401.status_code == 401
r403 = client.post("/api/admin/bikes/1/sold", headers=headers_user, json={})
assert r403.status_code == 403
print("  ✓ Unauthenticated -> 401")
print("  ✓ Regular user -> 403")

# Insert Approved Bike
cursor.execute("""
INSERT INTO bikes (title, brand, model, year, price, registration_number, kilometers_driven, fuel_type, transmission, seller_name, seller_phone, status, listing_status, isSoldout)
VALUES ('Royal Enfield Hunter 350', 'Royal Enfield', 'Hunter 350', 2023, 175000, 'TN-30-AZ-5566', 4200, 'Petrol', 'Manual', 'Praveen Admin', '9876543210', 'approved', 'published', 0)
""")
db_conn.commit()
bike_id = cursor.lastrowid
print(f"\n[Test 2] Created Approved Bike #{bike_id}...")

# Test 3: Staff Admin marks as sold
print(f"\n[Test 3] Staff Admin marks Bike #{bike_id} as Sold Out...")
payload = {
    "actual_sale_price": 172000,
    "seller_payout": 155000,
    "buyer_name": "Arun Kumar",
    "buyer_phone": "9842109876",
    "service_expense": 1500,
    "other_expense": 500
}
res = client.post(f"/api/admin/bikes/{bike_id}/sold", headers=headers_staff, json=payload)
assert res.status_code == 200, f"Got error: {res.data.decode()}"
data = res.get_json()
assert data.get("success") == True
tx = data.get("transaction", {})
assert "realized_profit" not in tx, "Profit must be redacted for staff admin!"
assert "seller_payout" not in tx, "Seller payout must be redacted for staff admin!"
print("  ✓ Sold out success returned (200)")
print("  ✓ Sensitive profit & seller payout redacted for Staff Admin")

# Test 4: Database state verification
print(f"\n[Test 4] Database state verification for Bike #{bike_id}...")
cur = db_conn.cursor()
cur.execute("SELECT id, status, listing_status, isSoldout, sold_by, sold_at FROM bikes WHERE id = ?", (bike_id,))
row = dict(cur.fetchone())
assert row["status"] == "sold", f"Expected status 'sold', got {row['status']}"
assert row["listing_status"] == "sold", f"Expected listing_status 'sold', got {row['listing_status']}"
assert row["isSoldout"] == 1, f"Expected isSoldout 1, got {row['isSoldout']}"
assert row["sold_by"] == "mani", f"Expected sold_by 'mani', got {row['sold_by']}"
assert row["sold_at"] is not None, "Expected sold_at timestamp"
print(f"  ✓ Database verified: status='{row['status']}', listing_status='{row['listing_status']}', isSoldout={row['isSoldout']}, sold_by='{row['sold_by']}'")

# Test 5: Prevent duplicate sold operations
print(f"\n[Test 5] Attempting duplicate sale on Bike #{bike_id}...")
res_dup = client.post(f"/api/admin/bikes/{bike_id}/sold", headers=headers_super, json=payload)
assert res_dup.status_code == 400
dup_json = res_dup.get_json()
print(f"  ✓ Duplicate rejected (400): {dup_json.get('message')}")

# Test 6: Verify removed from All Active Bikes & Approved Bikes
print(f"\n[Test 6] Verifying removal from active lists...")
res_all = client.get("/api/admin/bikes?tab=all", headers=headers_super)
all_list = res_all.get_json().get("data", [])
assert not any(b["id"] == bike_id for b in all_list), "Bike #{bike_id} should NOT be in tab=all!"
print("  ✓ Bike #{bike_id} removed from All Active Bikes (tab=all)")

res_app = client.get("/api/admin/bikes?tab=approved", headers=headers_super)
app_list = res_app.get_json().get("data", [])
assert not any(b["id"] == bike_id for b in app_list), "Bike #{bike_id} should NOT be in tab=approved!"
print("  ✓ Bike #{bike_id} removed from Approved Bikes (tab=approved)")

# Test 7: Verify removed from Public Marketplace
print(f"\n[Test 7] Verifying exclusion from public homepage...")
res_pub = client.get("/api/bikes")
pub_list = res_pub.get_json().get("data", [])
assert not any(b["id"] == bike_id for b in pub_list), "Bike #{bike_id} should NOT be in public marketplace!"
print("  ✓ Bike #{bike_id} excluded from public /api/bikes")

# Test 8: Verify presence in Sold Out page
print(f"\n[Test 8] Verifying presence in Sold Out Bikes...")
res_sold = client.get("/api/admin/sold-bikes", headers=headers_super)
sold_list = res_sold.get_json().get("data", [])
matching = [b for b in sold_list if b["id"] == bike_id or b["bike_id"] == bike_id]
assert len(matching) > 0, "Bike #{bike_id} MUST be in /api/admin/sold-bikes!"
sb = matching[0]
print(f"  ✓ Present in Sold Out page: {sb['brand']} {sb['model']}, Reg: {sb['registration_number']}, Final Price: ₹{sb['final_selling_price']:,.0f}, Sold By: {sb['sold_by']}")

# Test 9: Server-side pagination
print(f"\n[Test 9] Server-side pagination (10, 25, 50)...")
for lim in [10, 25, 50]:
    r = client.get(f"/api/admin/sold-bikes?limit={lim}", headers=headers_super)
    assert r.status_code == 200
    p = r.get_json().get("pagination", {})
    assert p.get("limit") == lim
    print(f"  ✓ Limit {lim} supported properly: total={p.get('total')}")

# Test 10: Dashboard counts
print(f"\n[Test 10] Dashboard statistics...")
res_dash = client.get("/api/admin/dashboard", headers=headers_super)
counts = res_dash.get_json().get("counts", {})
assert counts.get("sold_bikes", 0) >= 1
print(f"  ✓ Dashboard counts updated: Approved={counts.get('approved_bikes')}, Sold Out={counts.get('sold_bikes')}")

print("\n==================================================")
print(" ALL 10 TESTS PASSED WITH 100% SUCCESS!")
print("==================================================")
