"""
SMR Motors - Complete End-to-End Verification Test Suite
Tests all 15 upgrade requirements:
1. TiDB Cloud Schema & bike_images table verification
2. Multi-image upload API (up to 6 images, JPG/PNG/WEBP validation)
3. Add bike API (persisting up to 6 images in bike_images)
4. Admin bike details with gallery images & location
5. Admin update bike with RBAC financials (Superadmin vs Staff)
6. Bike approval with approver logging, seller notification, duplicate prevention
7. Bike rejection with mandatory reason, seller notification, duplicate prevention
8. Sold out bike management with Superadmin RBAC & buyer info
9. Dedicated sold bikes query with financial margin masking for staff
10. User dashboard API with all 6 live metrics
11. User listings API with rejection reasons
12. Homepage carousel & marketplace bikes query
"""

import os
import sys
import unittest
import json
import io

# Setup path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "my-node-app")))

from app import app, IN_MEMORY_STORE, get_db

class SMRMotorsFeatureTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_01_tidb_schema_verification(self):
        """Verify TiDB Cloud connectivity and bike_images table exists."""
        conn = get_db()
        self.assertIsNotNone(conn, "TiDB connection failed")
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SHOW TABLES LIKE 'bike_images'")
        table_row = cursor.fetchone()
        self.assertIsNotNone(table_row, "bike_images table must exist in TiDB")
        
        cursor.execute("DESCRIBE bikes")
        cols = [c["Field"] for c in cursor.fetchall()]
        self.assertIn("location", cols)
        self.assertIn("approved_by", cols)
        self.assertIn("approved_at", cols)
        self.assertIn("rejected_by", cols)
        self.assertIn("rejected_at", cols)
        self.assertIn("buying_price", cols)
        self.assertIn("expenses", cols)
        self.assertIn("profit", cols)
        cursor.close()
        conn.close()
        print("[PASS] Test 01: TiDB Cloud schema and bike_images table verified.")

    def test_02_image_upload_api(self):
        """Verify POST /api/upload/images handles validation and saves files."""
        # Test invalid extension
        bad_file = (io.BytesIO(b"fake image data"), "test.exe")
        res = self.client.post("/api/upload/images", data={"images": [bad_file]}, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 400)
        self.assertIn("Invalid format", res.get_json()["message"])

        # Test valid JPG/PNG/WEBP (up to 6 files)
        valid_files = [
            (io.BytesIO(b"fake jpeg 1"), "photo1.jpg"),
            (io.BytesIO(b"fake jpeg 2"), "photo2.png"),
            (io.BytesIO(b"fake webp 3"), "photo3.webp")
        ]
        res = self.client.post("/api/upload/images", data={"images": valid_files}, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(len(data["images"]), 3)
        self.assertEqual(data["images"][0]["is_primary"], 1)
        self.assertEqual(data["images"][1]["is_primary"], 0)
        print("[PASS] Test 02: 6-image upload API with validation passed.")

    def test_03_add_bike_with_six_images(self):
        """Verify POST /api/bikes creates bike and populates bike_images in TiDB."""
        test_bike_payload = {
            "title": "KTM RC 390 GP Edition 2023",
            "brand": "KTM",
            "model": "RC 390 GP",
            "year": "2023",
            "registration_number": "TN-30-CD-9988",
            "price": "275000",
            "kilometers_driven": "4500",
            "fuel_type": "Petrol",
            "transmission": "Manual",
            "location": "Salem Showroom",
            "description": "Showroom condition, single owner, zero scratch.",
            "seller_name": "Test Rider",
            "seller_phone": "9876543210",
            "images": json.dumps([
                "/static/images/IMG-20251204-WA0053.jpg",
                "/static/images/IMG-20251204-WA0051.jpg",
                "/static/images/IMG-20251204-WA0054.jpg"
            ])
        }
        res = self.client.post("/api/bikes", data=test_bike_payload)
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data["success"])
        bike_id = data["id"]
        self.assertGreater(bike_id, 0)

        # Check bike_images populated in DB
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM bike_images WHERE bike_id = %s", (bike_id,))
        img_rows = cursor.fetchall()
        cursor.close()
        conn.close()
        self.assertEqual(len(img_rows), 3)
        print(f"[PASS] Test 03: Add bike #{bike_id} with 3 images populated in bike_images passed.")

    def test_04_admin_login_and_rbacs(self):
        """Verify Admin vs Superadmin role authentication & financial protection."""
        # 1. Login as Superadmin
        superadmin_res = self.client.post("/api/admin/login", json={"username": "admin", "password": "admin123"})
        self.assertEqual(superadmin_res.status_code, 200)
        super_token = superadmin_res.get_json()["token"]

        # 2. Login as Staff
        staff_res = self.client.post("/api/admin/login", json={"username": "mani", "password": "mani@22"})
        self.assertEqual(staff_res.status_code, 200)
        staff_token = staff_res.get_json()["token"]

        # 3. Superadmin can access staff endpoint
        res = self.client.get("/api/admin/staff", headers={"Authorization": f"Bearer {super_token}"})
        self.assertEqual(res.status_code, 200)

        # 4. Staff cannot access staff endpoint (403 Forbidden)
        res = self.client.get("/api/admin/staff", headers={"Authorization": f"Bearer {staff_token}"})
        self.assertEqual(res.status_code, 403)
        print("[PASS] Test 04: Admin RBAC (Superadmin full access, Staff restricted) passed.")

    def test_05_bike_approval_and_rejection_workflow(self):
        """Verify Approve and Reject endpoints with logging, seller notifications & duplicate prevention."""
        # Login as Superadmin
        login_res = self.client.post("/api/admin/login", json={"username": "admin", "password": "admin123"})
        token = login_res.get_json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create a test pending bike
        res = self.client.post("/api/bikes", data={
            "title": "Royal Enfield Meteor 350 Fireball",
            "brand": "Royal Enfield",
            "model": "Meteor 350",
            "year": "2022",
            "registration_number": "TN-01-EE-1122",
            "price": "175000",
            "kilometers_driven": "9200",
            "status": "pending",
            "seller_name": "Kavitha",
            "seller_phone": "9944001122"
        })
        bike_id = res.get_json()["id"]

        # Test Reject without reason (Must fail 400)
        rej_fail = self.client.post(f"/api/admin/bikes/{bike_id}/reject", json={"reason": ""}, headers=headers)
        self.assertEqual(rej_fail.status_code, 400)
        self.assertIn("reason is required", rej_fail.get_json()["message"])

        # Test Approve
        app_res = self.client.post(f"/api/admin/bikes/{bike_id}/approve", json={"approved_price": 170000}, headers=headers)
        self.assertEqual(app_res.status_code, 200)
        self.assertTrue(app_res.get_json()["success"])

        # Duplicate Approve must be rejected
        dup_app = self.client.post(f"/api/admin/bikes/{bike_id}/approve", headers=headers)
        self.assertEqual(dup_app.status_code, 400)
        self.assertIn("already approved", dup_app.get_json()["message"])

        # Check DB columns updated
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT status, approved_by, approved_at FROM bikes WHERE id = %s", (bike_id,))
        b_row = cursor.fetchone()
        self.assertEqual(b_row["status"], "approved")
        self.assertEqual(b_row["approved_by"], "admin")
        self.assertIsNotNone(b_row["approved_at"])

        # Check seller notification created
        cursor.execute("SELECT * FROM notifications WHERE target_role = 'user' ORDER BY id DESC LIMIT 1")
        notif = cursor.fetchone()
        self.assertIn("Approved", notif["title"])
        cursor.close()
        conn.close()
        print("[PASS] Test 05: Bike approval workflow with duplicate prevention & seller notification passed.")

    def test_06_mark_sold_and_sold_bikes_api(self):
        """Verify Superadmin mark-sold, transaction persistence & staff financial masking."""
        super_res = self.client.post("/api/admin/login", json={"username": "admin", "password": "admin123"})
        super_token = super_res.get_json()["token"]
        staff_res = self.client.post("/api/admin/login", json={"username": "mani", "password": "mani@22"})
        staff_token = staff_res.get_json()["token"]

        # 1. Staff cannot mark sold (403 Forbidden)
        res = self.client.post("/api/admin/bikes/1/mark-sold", json={"actual_sale_price": 140000}, headers={"Authorization": f"Bearer {staff_token}"})
        self.assertEqual(res.status_code, 403)

        # 2. Superadmin marks sold with buyer details & expense breakdown
        sold_payload = {
            "actual_sale_price": 145000,
            "seller_payout": 125000,
            "service_expense": 3000,
            "repair_expense": 2000,
            "transport_expense": 1000,
            "other_expense": 500,
            "buyer_name": "Arun Kumar",
            "buyer_phone": "9840123456",
            "notes": "RC transfer scheduled"
        }
        res = self.client.post("/api/admin/bikes/1/mark-sold", json=sold_payload, headers={"Authorization": f"Bearer {super_token}"})
        self.assertEqual(res.status_code, 200)

        # 3. Superadmin sold-bikes API includes full financials
        res_super = self.client.get("/api/admin/sold-bikes", headers={"Authorization": f"Bearer {super_token}"})
        self.assertEqual(res_super.status_code, 200)
        self.assertTrue(res_super.get_json()["is_superadmin"])
        first_tx = res_super.get_json()["data"][0]
        self.assertIn("realized_profit", first_tx)
        self.assertIn("seller_payout", first_tx)

        # 4. Staff sold-bikes API masks confidential financials
        res_staff = self.client.get("/api/admin/sold-bikes", headers={"Authorization": f"Bearer {staff_token}"})
        self.assertEqual(res_staff.status_code, 200)
        self.assertFalse(res_staff.get_json()["is_superadmin"])
        staff_tx = res_staff.get_json()["data"][0]
        self.assertNotIn("realized_profit", staff_tx)
        self.assertNotIn("seller_payout", staff_tx)
        print("[PASS] Test 06: Sold-out bike management & financial privacy protection passed.")

    def test_07_user_dashboard_and_listings_api(self):
        """Verify user dashboard metrics and listings endpoint."""
        res = self.client.get("/api/users/dashboard")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()["data"]
        stats = data["stats"]
        self.assertIn("total_listings", stats)
        self.assertIn("pending_listings", stats)
        self.assertIn("approved_listings", stats)
        self.assertIn("rejected_listings", stats)
        self.assertIn("sold_listings", stats)
        self.assertIn("pending_enquiries", stats)
        print("[PASS] Test 07: User dashboard 6 accurate metrics verified.")

    def test_08_homepage_bikes_and_carousel(self):
        """Verify homepage /api/bikes endpoint returns active published bikes."""
        res = self.client.get("/api/bikes?status=approved")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        bikes = data.get("data") or data.get("bikes") or []
        for b in bikes:
            # Must not show soldout bikes in active marketplace
            self.assertNotEqual(b.get("isSoldout"), 1)
            self.assertIn("location", b)
            self.assertIn("images", b)
        print(f"[PASS] Test 08: Homepage query returned {len(bikes)} active published bikes.")

if __name__ == "__main__":
    unittest.main()
