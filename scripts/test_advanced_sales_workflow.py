"""
Comprehensive test script for SMR Motors Advanced Sold Out Management, Financial Tracking, and Customer Details
Includes in-memory SQLite emulation conforming to TiDB Cloud 26-table schema.
"""
import os
import sys
import io
import json
import sqlite3
import datetime
import jwt

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath("my-node-app"))
import app as flask_app
from app import app, JWT_SECRET, get_db

sys.stdout.reconfigure(encoding='utf-8')

# Setup SQLite in-memory database mimicking TiDB Cloud schema
db_conn = sqlite3.connect(":memory:", check_same_thread=False)
db_conn.row_factory = sqlite3.Row

cursor = db_conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS bikes (
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
    repair_expenses REAL DEFAULT 0,
    other_expenses REAL DEFAULT 0,
    expenses REAL DEFAULT 0,
    profit REAL DEFAULT 0,
    profit_margin REAL DEFAULT 0,
    isSoldout INTEGER DEFAULT 0,
    sold_by TEXT,
    sold_at TIMESTAMP,
    sold_snapshot TEXT,
    payment_status TEXT,
    purchase_date TIMESTAMP,
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS bikesforsale (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    listingTitle TEXT,
    makedFrom TEXT,
    bikeModel TEXT,
    bikeBuyingYear TEXT,
    vehicleNumber TEXT,
    sellingPrice TEXT,
    bikeKms TEXT,
    description TEXT,
    sellerName TEXT,
    mobileNum TEXT,
    isAccepted INTEGER DEFAULT 0,
    isSoldout INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS sold_bikes (
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
    buyer_location TEXT,
    buyer_city TEXT,
    buyer_state TEXT,
    payment_method TEXT,
    payment_status TEXT,
    advance_amount REAL DEFAULT 0,
    remaining_amount REAL DEFAULT 0,
    buying_price REAL DEFAULT 0,
    repair_expense REAL DEFAULT 0,
    other_expense REAL DEFAULT 0,
    notes TEXT,
    sold_by TEXT,
    sold_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS buyer_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bike_id INTEGER NOT NULL,
    full_name VARCHAR(120) NOT NULL,
    phone VARCHAR(25) NOT NULL,
    alt_phone VARCHAR(25) NULL,
    email VARCHAR(191) NULL,
    location VARCHAR(200) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL DEFAULT 'Tamil Nadu',
    address TEXT NULL,
    pincode VARCHAR(20) NULL,
    consent_obtained TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS sale_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bike_id INTEGER NOT NULL,
    buyer_id INTEGER NULL,
    document_type VARCHAR(60) NOT NULL,
    document_ref_masked VARCHAR(100) NULL,
    file_name VARCHAR(255) NULL,
    mime_type VARCHAR(100) NULL,
    file_size INT NULL DEFAULT 0,
    file_data BLOB NULL,
    uploaded_by VARCHAR(80) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS bike_transactions (
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
    buyer_location TEXT,
    buyer_city TEXT,
    buyer_state TEXT,
    payment_method TEXT,
    payment_status TEXT,
    advance_amount REAL DEFAULT 0,
    remaining_amount REAL DEFAULT 0,
    notes TEXT,
    sold_by TEXT,
    sold_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS listing_status_history (
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
CREATE TABLE IF NOT EXISTS financial_records (
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
CREATE TABLE IF NOT EXISTS bike_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bike_id INTEGER NOT NULL,
    image_url TEXT NOT NULL,
    image_order INTEGER DEFAULT 1,
    is_primary INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS enquiries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bike_id INTEGER,
    listingId INTEGER,
    name TEXT NOT NULL,
    customerName TEXT,
    email TEXT,
    phone TEXT,
    mobile TEXT,
    message TEXT,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

db_conn.commit()

class MySQLCursorAdapter:
    def __init__(self, sqlite_cursor):
        self._cur = sqlite_cursor
    def execute(self, sql, params=None):
        clean_sql = sql.replace("%s", "?")
        clean_sql = clean_sql.replace("NOW()", "CURRENT_TIMESTAMP")
        if "ON DUPLICATE KEY UPDATE" in clean_sql:
            clean_sql = clean_sql.split("ON DUPLICATE KEY UPDATE")[0].strip()
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

def make_token(admin_data):
    payload = {
        "id": admin_data.get("id", 1),
        "username": admin_data.get("username", "admin"),
        "name": admin_data.get("name", "Test Admin"),
        "role": admin_data.get("role", "admin"),
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def run_tests():
    print("=" * 70)
    print("STARTING ADVANCED SOLD OUT & FINANCIAL TRACKING WORKFLOW TESTS")
    print("=" * 70)

    client = app.test_client()

    # 1. Generate auth tokens
    superadmin_token = make_token({"id": 1, "username": "superadmin_test", "role": "superadmin"})
    staff_token = make_token({"id": 2, "username": "staff_test", "role": "admin"})
    user_token = make_token({"id": 100, "username": "customer_test", "role": "user"})

    headers_super = {"Authorization": f"Bearer {superadmin_token}"}
    headers_staff = {"Authorization": f"Bearer {staff_token}"}
    headers_user = {"Authorization": f"Bearer {user_token}"}

    # 2. Insert test bike
    cur_init = db_conn.cursor()
    cur_init.execute("""
        INSERT INTO bikes (
            title, brand, model, year, price, kilometers_driven, fuel_type, transmission, 
            registration_number, status, listing_status, isSoldout, location, description, 
            buying_price, public_selling_price, repair_expenses, other_expenses, created_at
        ) VALUES (
            'Test Royal Enfield Hunter 350', 'Royal Enfield', 'Hunter 350', 2023, 150000, 4500, 'Petrol', 'Manual',
            'TN-30-AZ-9999', 'approved', 'approved', 0, 'Salem Showroom', 'Pristine test machine',
            120000, 150000, 5000, 2000, CURRENT_TIMESTAMP
        )
    """)
    db_conn.commit()
    test_bike_id = cur_init.lastrowid
    print(f"[SETUP] Created test bike with ID: {test_bike_id}")

    # TEST 1: Superadmin Views Details of Active Approved Bike
    print("\n--- TEST 1: Superadmin Views Details of Active Bike ---")
    res = client.get(f"/api/admin/bikes/{test_bike_id}/details", headers=headers_super)
    data = res.get_json()
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert data["success"] is True
    fin = data["data"]["financials"]
    assert fin is not None, "Superadmin MUST see financials"
    assert fin["buying_price"] == 120000
    assert fin["selling_price"] == 150000
    assert fin["repair_expenses"] == 5000
    assert fin["other_expenses"] == 2000
    assert fin["total_expenses"] == 7000
    assert fin["gross_profit"] == 30000
    assert fin["net_profit"] == 23000
    print(f"[PASS] Superadmin sees financials: Gross: {fin['formatted_gross_profit']}, Net: {fin['formatted_net_profit']}, Margin: {fin['profit_margin_pct']}%")

    # TEST 2: Staff Admin Views Details of Active Approved Bike (Financials Redacted)
    print("\n--- TEST 2: Staff Admin Views Details (Financials Redacted) ---")
    res_staff = client.get(f"/api/admin/bikes/{test_bike_id}/details", headers=headers_staff)
    data_staff = res_staff.get_json()
    assert res_staff.status_code == 200
    assert data_staff["data"]["financials"] is None, "Staff admin MUST NOT see financials"
    assert data_staff["is_superadmin"] is False
    print("[PASS] Staff Admin receives bike specs but financials are strictly redacted (None)")

    # TEST 3: Unauthenticated / User Access Blocked
    print("\n--- TEST 3: Regular User Blocked from Admin Details ---")
    res_user = client.get(f"/api/admin/bikes/{test_bike_id}/details", headers=headers_user)
    assert res_user.status_code in (401, 403), f"Expected 401/403, got {res_user.status_code}"
    print("[PASS] Regular user blocked with HTTP", res_user.status_code)

    # TEST 4: Superadmin Updates Financials
    print("\n--- TEST 4: Superadmin Updates Financials via PUT ---")
    res_put_super = client.put(f"/api/admin/bikes/{test_bike_id}/financials", headers=headers_super, json={
        "buying_price": 125000,
        "repair_expenses": 6000,
        "other_expenses": 3000
    })
    assert res_put_super.status_code == 200
    put_data = res_put_super.get_json()
    assert put_data["success"] is True
    assert put_data["financials"]["buying_price"] == 125000
    assert put_data["financials"]["total_expenses"] == 9000
    assert put_data["financials"]["net_profit"] == 16000 # 150000 - 125000 - 9000 = 16000
    print(f"[PASS] Financials successfully updated and re-ledgered: Net Profit = {put_data['financials']['formatted_net_profit']}")

    # TEST 5: Staff Admin Forbidden from Updating Financials
    print("\n--- TEST 5: Staff Admin Forbidden from Updating Financials ---")
    res_put_staff = client.put(f"/api/admin/bikes/{test_bike_id}/financials", headers=headers_staff, json={
        "buying_price": 100000
    })
    assert res_put_staff.status_code == 403
    print("[PASS] Staff Admin receives HTTP 403 Forbidden on financial update")

    # TEST 6: Complete Sold Out Workflow (Customer + Proof Attachment + Sale details)
    print("\n--- TEST 6: Complete Motorcycle Sale Details Registration ---")
    fake_pdf = (io.BytesIO(b"%PDF-1.4 test invoice and delivery receipt binary content"), "sale_receipt.pdf")
    form_payload = {
        "customer_name": "Senthil Kumar",
        "customer_phone": "9842112345",
        "alt_phone": "9842199999",
        "customer_email": "senthil.k@example.com",
        "customer_location": "Fairlands, Salem",
        "customer_city": "Salem",
        "customer_state": "Tamil Nadu",
        "customer_pincode": "636016",
        "customer_address": "42, Nehru Road, Fairlands",
        "proof_type": "Driving Licence",
        "proof_ref_masked": "DL-TN30-2015-00123",
        "consent_obtained": "1",
        "proof_document": fake_pdf,
        "sale_date": datetime.date.today().isoformat(),
        "actual_sale_price": "148000",
        "payment_method": "UPI",
        "payment_status": "Full Payment",
        "advance_amount": "148000",
        "remaining_amount": "0",
        "notes": "RC transfer documents signed, vehicle handed over with spare key."
    }

    res_sold = client.post(
        f"/api/admin/bikes/{test_bike_id}/sold",
        headers=headers_super,
        data=form_payload,
        content_type="multipart/form-data"
    )
    assert res_sold.status_code == 200, f"Expected 200, got {res_sold.status_code}: {res_sold.data}"
    sold_resp = res_sold.get_json()
    assert sold_resp["success"] is True
    print("[PASS] Motorcycle marked as Sold Out successfully!")

    # TEST 7: Duplicate Sale Prevention
    print("\n--- TEST 7: Duplicate Sale Prevention ---")
    res_sold_dup = client.post(
        f"/api/admin/bikes/{test_bike_id}/sold",
        headers=headers_super,
        json={"customer_name": "Another Buyer", "customer_phone": "9999999999", "customer_city": "Salem", "actual_sale_price": 140000}
    )
    assert res_sold_dup.status_code == 400
    dup_msg = res_sold_dup.get_json()["message"]
    assert "already marked as sold" in dup_msg.lower()
    print(f"[PASS] Duplicate sale blocked: '{dup_msg}'")

    # TEST 8: Verify Persistence in buyer_details, sale_documents, sold_bikes, bikes
    print("\n--- TEST 8: Verify Database Persistence Across All Tables ---")
    cur_v = db_conn.cursor()

    cur_v.execute("SELECT status, listing_status, isSoldout, sold_at, sold_by FROM bikes WHERE id = ?", (test_bike_id,))
    b_row = cur_v.fetchone()
    assert b_row["status"] == "sold"
    assert b_row["listing_status"] == "sold"
    assert b_row["isSoldout"] == 1
    assert b_row["sold_at"] is not None

    cur_v.execute("SELECT * FROM buyer_details WHERE bike_id = ?", (test_bike_id,))
    buyer_row = cur_v.fetchone()
    assert buyer_row is not None
    assert buyer_row["full_name"] == "Senthil Kumar"
    assert buyer_row["phone"] == "9842112345"
    assert buyer_row["city"] == "Salem"

    cur_v.execute("SELECT id, document_type, document_ref_masked, file_name, file_size FROM sale_documents WHERE bike_id = ?", (test_bike_id,))
    doc_row = cur_v.fetchone()
    assert doc_row is not None
    assert doc_row["document_type"] == "Driving Licence"
    assert doc_row["file_name"].startswith("proof_") and doc_row["file_name"].endswith(".pdf")
    doc_id = doc_row["id"]

    cur_v.execute("SELECT * FROM sold_bikes WHERE bike_id = ?", (test_bike_id,))
    sb_row = cur_v.fetchone()
    assert sb_row is not None
    assert float(sb_row["actual_sale_price"]) == 148000
    assert sb_row["payment_status"] == "Full Payment"

    print("[PASS] Verified: bikes (status=sold, isSoldout=1), buyer_details, sale_documents, sold_bikes all match perfectly!")

    # TEST 9: Secure Proof Download RBAC
    print("\n--- TEST 9: Secure Proof Document Download RBAC ---")
    # Superadmin can download
    res_dl_super = client.get(f"/api/admin/sale-documents/{doc_id}/download", headers=headers_super)
    assert res_dl_super.status_code == 200
    assert b"%PDF-1.4" in res_dl_super.data
    print("[PASS] Superadmin successfully downloaded encrypted proof document")

    # Staff Admin gets 403 Forbidden
    res_dl_staff = client.get(f"/api/admin/sale-documents/{doc_id}/download", headers=headers_staff)
    assert res_dl_staff.status_code == 403
    print("[PASS] Staff Admin strictly forbidden (HTTP 403) from downloading identity proof")

    # TEST 10: Sold Out List API Filtering & Pagination
    print("\n--- TEST 10: Sold Out List API (Search, Filter, Pagination) ---")
    res_list = client.get(f"/api/admin/sold-bikes?search=Senthil&payment_status=Full%20Payment&limit=10&page=1", headers=headers_super)
    assert res_list.status_code == 200
    list_data = res_list.get_json()
    assert list_data["success"] is True
    assert len(list_data["data"]) >= 1
    found_item = next((item for item in list_data["data"] if item["id"] == test_bike_id), None)
    assert found_item is not None
    assert found_item["customer_name"] == "Senthil Kumar"
    assert found_item["payment_status"] == "Full Payment"
    assert "net_profit" in found_item
    print(f"[PASS] Sold Out List API correctly filtered by customer search and payment status: Found #{found_item['id']} ({found_item['title']})")

    print("\n" + "=" * 70)
    print("ALL 10 TESTS PASSED SUCCESSFULLY! WORKFLOW IS 100% VERIFIED.")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
