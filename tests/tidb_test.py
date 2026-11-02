import os
import sys
import unittest

# Ensure path includes my-node-app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "my-node-app"))

import app

class TiDBIntegrationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("\n======================================================")
        print("  STARTING TiDB CLOUD LIVE VERIFICATION TEST SUITE")
        print("======================================================")
        # Verify db configuration
        cls.db_name = os.getenv("DB_NAME", "smr_motors")
        cls.host = os.getenv("DB_HOST", "gateway01.ap-southeast-1.prod.aws.tidbcloud.com")
        print(f"Target Cluster: {cls.host}:4000 (Database: {cls.db_name})")

    def test_01_sys_database_guard(self):
        """Requirement 13: Never use the sys database for application data"""
        self.assertNotEqual(app.DB_NAME.lower(), "sys", "Security violation: sys database cannot be used for application data.")
        print("  [PASS] Requirement 13: Confirmed non-sys database ('{}')".format(app.DB_NAME))

    def test_02_database_connectivity(self):
        """Requirement 8: Test database connectivity with TLS verification"""
        conn = app.get_db()
        self.assertIsNotNone(conn, "Could not establish TLS connection to TiDB Cloud.")
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        self.assertEqual(row[0], 1)
        print("  [PASS] Requirement 8: TiDB Cloud TLS connectivity verified")

    def test_03_select_1(self):
        """Requirement 9: Test SELECT 1"""
        conn = app.get_db()
        self.assertIsNotNone(conn)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 AS probe")
        val = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        self.assertEqual(val, 1)
        print("  [PASS] Requirement 9: SELECT 1 probe returned: {}".format(val))

    def test_04_tables_exist(self):
        """Requirement 6: Verify all required application tables exist"""
        conn = app.get_db()
        self.assertIsNotNone(conn)
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = [r[0].lower() for r in cursor.fetchall()]
        cursor.close()
        conn.close()
        required_tables = ["users", "bikes", "enquiries", "categories", "contact_messages", "admins", "favorites", "admin_audit_logs", "bikesforsale"]
        for t in required_tables:
            self.assertIn(t, tables, f"Missing table: {t}")
        print(f"  [PASS] Requirement 6: All {len(required_tables)} application tables verified in TiDB: {tables}")

    def test_05_google_login_and_user_registration(self):
        """Requirement 10: Test user registration and Google login"""
        client = app.app.test_client()
        # Test mock Google verified token
        res = client.post("/api/auth/google", json={"credential": "test-mock-token-tidbtest"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertIn("token", data)
        self.assertEqual(data.get("user", {}).get("role"), "user")
        
        # Verify in TiDB users table
        conn = app.get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", ("tidbtest@gmail.com",))
        user_row = cursor.fetchone()
        cursor.close()
        conn.close()
        self.assertIsNotNone(user_row)
        self.assertEqual(user_row["email"], "tidbtest@gmail.com")
        print("  [PASS] Requirement 10: Google user registered and verified in TiDB Cloud: {}".format(user_row["email"]))

    def test_06_bike_listings(self):
        """Requirement 10: Test bike listings (Add + Retrieve)"""
        client = app.app.test_client()
        new_bike_payload = {
            "title": "KTM Duke 390 Test Edition",
            "brand": "KTM",
            "model": "Duke 390",
            "year": 2023,
            "price": 285000,
            "kilometers_driven": 4500,
            "fuel_type": "Petrol",
            "transmission": "Manual",
            "seller_name": "Test Seller",
            "seller_phone": "9876543210"
        }
        res = client.post("/api/bikes", json=new_bike_payload)
        self.assertEqual(res.status_code, 201)
        bike_id = res.get_json().get("id")
        self.assertIsNotNone(bike_id)

        # Query via GET /api/bikes
        res_list = client.get("/api/bikes")
        self.assertEqual(res_list.status_code, 200)
        bikes = res_list.get_json().get("bikes", [])
        self.assertTrue(any(b.get("title") == "KTM Duke 390 Test Edition" for b in bikes))
        print("  [PASS] Requirement 10: Bike listing created and retrieved from TiDB (id: {})".format(bike_id))

    def test_07_customer_enquiries(self):
        """Requirement 10: Test enquiries submission and retrieval"""
        client = app.app.test_client()
        enq_payload = {
            "name": "Arun Kumar",
            "email": "arun.kumar@example.com",
            "phone": "9876543210",
            "message": "Interested in test riding this motorcycle."
        }
        res = client.post("/api/enquiries", json=enq_payload)
        self.assertEqual(res.status_code, 201)
        enq_id = res.get_json().get("id")
        self.assertIsNotNone(enq_id)

        # Verify in TiDB Cloud
        conn = app.get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM enquiries WHERE id = %s", (enq_id,))
        enq_row = cursor.fetchone()
        cursor.close()
        conn.close()
        self.assertIsNotNone(enq_row)
        print("  [PASS] Requirement 10: Customer enquiry persisted to TiDB Cloud (id: {})".format(enq_id))

    def test_08_admin_operations(self):
        """Requirement 10: Test admin login, vehicle approval and price update"""
        client = app.app.test_client()
        # Admin login
        res_login = client.post("/api/admin/login", json={"username": "admin", "password": "admin123"})
        self.assertEqual(res_login.status_code, 200)
        admin_token = res_login.get_json().get("token")
        self.assertIsNotNone(admin_token)

        # Admin approve bike
        res_approve = client.put("/api/admin/bikes/1/approve", headers={"Authorization": f"Bearer {admin_token}"})
        self.assertEqual(res_approve.status_code, 200)

        # Admin update price
        res_price = client.put("/api/admin/bikes/1/price", json={"price": 149000}, headers={"Authorization": f"Bearer {admin_token}"})
        self.assertEqual(res_price.status_code, 200)

        # Admin telemetry dashboard
        res_dash = client.get("/api/admin/dashboard", headers={"Authorization": f"Bearer {admin_token}"})
        self.assertEqual(res_dash.status_code, 200)
        self.assertIn("counts", res_dash.get_json().get("data", {}))
        print("  [PASS] Requirement 10: Admin operations (Login, Approve, Price, Dashboard) validated on TiDB")

if __name__ == "__main__":
    unittest.main()
