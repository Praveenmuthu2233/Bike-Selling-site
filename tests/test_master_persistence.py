"""
Comprehensive Test Suite for SMR Motors Permanent TiDB Cloud Persistence
Validates all 13 Scenarios required by the Master Specification.
"""

import os
import sys
import json
import time
import unittest
import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_DIR = os.path.join(BASE_DIR, "my-node-app")
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import app, get_db, save_durable_image, JWT_SECRET, UPLOAD_DIR
import jwt


class MasterPersistenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        cls.client = app.test_client()

        conn = get_db()
        assert conn is not None, "TiDB Cloud connection failed!"
        cls.conn = conn

        # Create auth tokens
        cls.superadmin_token = jwt.encode(
            {"id": 1, "username": "admin", "role": "superadmin", "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)},
            JWT_SECRET,
            algorithm="HS256"
        )
        cls.superadmin_headers = {
            "Authorization": f"Bearer {cls.superadmin_token}",
            "Content-Type": "application/json"
        }

        cls.admin_token = jwt.encode(
            {"id": 2, "username": "staff1", "role": "admin", "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)},
            JWT_SECRET,
            algorithm="HS256"
        )
        cls.admin_headers = {
            "Authorization": f"Bearer {cls.admin_token}",
            "Content-Type": "application/json"
        }

        # Clean up test data
        cursor = conn.cursor()
        cursor.execute("DELETE FROM bikes WHERE title LIKE 'TEST_MASTER_%'")
        cursor.execute("DELETE FROM users WHERE email LIKE 'master_test_%@smrmotors.com'")
        cursor.execute("DELETE FROM enquiries WHERE email LIKE 'master_test_%@smrmotors.com'")
        cursor.execute("DELETE FROM contact_messages WHERE email LIKE 'master_test_%@smrmotors.com'")
        cursor.execute("DELETE FROM durable_images WHERE filename LIKE 'master_test_%'")
        conn.commit()
        cursor.close()

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "conn") and cls.conn:
            try:
                cursor = cls.conn.cursor()
                cursor.execute("DELETE FROM bikes WHERE title LIKE 'TEST_MASTER_%'")
                cursor.execute("DELETE FROM users WHERE email LIKE 'master_test_%@smrmotors.com'")
                cursor.execute("DELETE FROM enquiries WHERE email LIKE 'master_test_%@smrmotors.com'")
                cursor.execute("DELETE FROM contact_messages WHERE email LIKE 'master_test_%@smrmotors.com'")
                cursor.execute("DELETE FROM durable_images WHERE filename LIKE 'master_test_%'")
                cls.conn.commit()
                cursor.close()
                cls.conn.close()
            except Exception:
                pass

    # =========================================================================
    # SCENARIO 1: User registers / logs in -> Stored permanently in TiDB users
    # =========================================================================
    def test_01_user_registration_and_session_persistence(self):
        """Scenario 1: User profile & session stored permanently in TiDB."""
        res = self.client.post("/api/auth/demo-google", json={"remember_me": True})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertIn("token", data)
        user = data.get("user")
        self.assertIsNotNone(user.get("id"))
        user_id = user["id"]

        # Verify directly in TiDB Cloud using fresh connection
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name, email, role FROM users WHERE id = %s", (user_id,))
        db_user = cursor.fetchone()
        cursor.close()
        conn.close()
        self.assertIsNotNone(db_user)
        self.assertEqual(db_user["email"], "rider@smrmotors.com")

        # Test profile update persists to TiDB
        user_headers = {"Authorization": f"Bearer {data['token']}"}
        update_res = self.client.put("/api/users/profile", json={"name": "Master Rider Test", "phone": "9876543210"}, headers=user_headers)
        self.assertEqual(update_res.status_code, 200)

        # Verify update in TiDB on fresh connection
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT name, phone FROM users WHERE id = %s", (user_id,))
        fresh_user = cursor.fetchone()
        cursor.close()
        conn.close()
        self.assertEqual(fresh_user["name"], "Master Rider Test")
        self.assertEqual(fresh_user["phone"], "9876543210")

    # =========================================================================
    # SCENARIO 2 & 3: User adds motorcycle listing -> Pending in TiDB -> Survives restart
    # =========================================================================
    def test_02_and_03_user_adds_bike_and_survives_restart(self):
        """Scenarios 2 & 3: User submits listing, stored as pending, survives restart."""
        user_token = jwt.encode(
            {"id": 1, "email": "master_test_user@smrmotors.com", "name": "Master Tester", "role": "user", "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)},
            JWT_SECRET,
            algorithm="HS256"
        )
        headers = {"Authorization": f"Bearer {user_token}", "Content-Type": "application/json"}

        payload = {
            "title": "TEST_MASTER_Royal Enfield Hunter 350",
            "brand": "Royal Enfield",
            "model": "Hunter 350",
            "year": 2023,
            "registration_number": "TN-01-AB-9999",
            "price": 145000,
            "kilometers_driven": 4500,
            "fuel_type": "Petrol",
            "transmission": "Manual",
            "location": "Chennai",
            "description": "Mint condition Hunter 350",
            "seller_name": "Master Tester",
            "seller_phone": "9888877777"
        }

        res = self.client.post("/api/bikes", json=payload, headers=headers)
        self.assertEqual(res.status_code, 201)
        res_data = res.get_json()
        self.assertTrue(res_data.get("success"))
        bike_id = res_data.get("id")
        self.assertIsNotNone(bike_id)
        MasterPersistenceTests.test_bike_id = bike_id

        # Direct TiDB verification on separate connection (simulating app restart)
        fresh_conn = get_db()
        cursor = fresh_conn.cursor(dictionary=True)
        cursor.execute("SELECT id, title, status, listing_status, price FROM bikes WHERE id = %s", (bike_id,))
        row = cursor.fetchone()
        cursor.close()
        fresh_conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row["title"], "TEST_MASTER_Royal Enfield Hunter 350")
        self.assertEqual(row["status"], "pending")
        self.assertEqual(row["listing_status"], "pending")
        self.assertEqual(float(row["price"]), 145000.0)

    # =========================================================================
    # SCENARIO 4 & 5: Admin approves bike -> Status 'approved' -> Visible on marketplace
    # =========================================================================
    def test_04_and_05_admin_approves_bike_and_homepage_visibility(self):
        """Scenarios 4 & 5: Admin approval commits permanently and appears in marketplace inventory."""
        bike_id = getattr(MasterPersistenceTests, "test_bike_id", None)
        self.assertIsNotNone(bike_id, "Bike ID from previous test missing")

        approve_res = self.client.put(f"/api/admin/bikes/{bike_id}/approve", json={"buying_price": 130000}, headers=self.admin_headers)
        self.assertEqual(approve_res.status_code, 200)
        self.assertTrue(approve_res.get_json().get("success"))

        # Verify TiDB directly on fresh connection
        fresh_conn = get_db()
        cursor = fresh_conn.cursor(dictionary=True)
        cursor.execute("SELECT id, status, listing_status, isSoldout FROM bikes WHERE id = %s", (bike_id,))
        row = cursor.fetchone()
        cursor.close()
        fresh_conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row["status"], "approved")
        self.assertIn(row["listing_status"], ("published", "approved"))
        self.assertEqual(row["isSoldout"], 0)

        # Scenario 5: Multiple consecutive queries to /api/bikes must reliably return the bike
        for i in range(5):
            inv_res = self.client.get("/api/bikes")
            self.assertEqual(inv_res.status_code, 200)
            inv_data = inv_res.get_json()
            all_bikes = inv_data.get("bikes") or inv_data.get("data") or []
            found = any(b.get("id") == bike_id for b in all_bikes)
            self.assertTrue(found, f"Approved bike #{bike_id} missing on inventory query iteration {i+1}")

    # =========================================================================
    # SCENARIO 6, 7 & 8: Mark Sold Out -> Appears in Sold Gallery -> Never in Active Inventory
    # =========================================================================
    def test_06_07_08_mark_sold_and_gallery_verification(self):
        """Scenarios 6, 7 & 8: Bike marked sold out permanently; moves to sold gallery; removed from active."""
        bike_id = getattr(MasterPersistenceTests, "test_bike_id", None)
        self.assertIsNotNone(bike_id)

        sold_payload = {
            "sold_price": 140000,
            "sale_price": 140000,
            "buyer_name": "Karthik Buyer",
            "buyer_phone": "9777766666",
            "buying_price": 125000,
            "service_expense": 2000,
            "repair_expense": 1000,
            "total_expenses": 3000
        }

        sold_res = self.client.post(f"/api/admin/bikes/{bike_id}/sold", json=sold_payload, headers=self.superadmin_headers)
        self.assertEqual(sold_res.status_code, 200)
        self.assertTrue(sold_res.get_json().get("success"))

        # Verify TiDB directly on fresh connection
        fresh_conn = get_db()
        cursor = fresh_conn.cursor(dictionary=True)
        cursor.execute("SELECT id, status, listing_status, isSoldout, price FROM bikes WHERE id = %s", (bike_id,))
        bike_row = cursor.fetchone()
        cursor.execute("SELECT * FROM sold_bikes WHERE bike_id = %s", (bike_id,))
        sold_row = cursor.fetchone()
        cursor.close()
        fresh_conn.close()

        self.assertEqual(bike_row["status"], "soldout")
        self.assertEqual(bike_row["isSoldout"], 1)
        self.assertIsNotNone(sold_row)
        self.assertEqual(sold_row["buyer_name"], "Karthik Buyer")

        # Scenario 7: Query Sold Out Gallery API (/api/sold-bikes)
        gallery_res = self.client.get("/api/sold-bikes")
        self.assertEqual(gallery_res.status_code, 200)
        gallery_data = gallery_res.get_json()
        sold_list = gallery_data.get("data") or gallery_data.get("bikes") or []
        found_in_sold = any(b.get("id") == bike_id for b in sold_list)
        self.assertTrue(found_in_sold, f"Sold bike #{bike_id} not found in sold gallery!")

        # Scenario 8: Must NEVER appear in active marketplace inventory
        active_res = self.client.get("/api/bikes")
        self.assertEqual(active_res.status_code, 200)
        active_bikes = active_res.get_json().get("bikes") or active_res.get_json().get("data") or []
        found_in_active = any(b.get("id") == bike_id for b in active_bikes)
        self.assertFalse(found_in_active, f"Sold bike #{bike_id} erroneously returned in active inventory!")

    # =========================================================================
    # SCENARIO 9 & 10: Enquiry Submission & Admin Reply Persistence
    # =========================================================================
    def test_09_and_10_enquiry_and_reply_persistence(self):
        """Scenarios 9 & 10: Enquiries and admin replies persist permanently in TiDB."""
        enq_payload = {
            "name": "Master Enquiry Test",
            "email": "master_test_enquiry@smrmotors.com",
            "phone": "9111122222",
            "message": "Is this motorcycle still available for immediate test ride?",
            "bike_title": "Hunter 350 Test"
        }

        sub_res = self.client.post("/api/enquiries", json=enq_payload)
        self.assertEqual(sub_res.status_code, 201)
        enq_id = sub_res.get_json().get("id")
        self.assertIsNotNone(enq_id)

        # Verify in TiDB directly on fresh connection
        fresh_conn = get_db()
        cursor = fresh_conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name, email, status FROM enquiries WHERE id = %s", (enq_id,))
        enq_row = cursor.fetchone()
        cursor.close()
        fresh_conn.close()

        self.assertIsNotNone(enq_row)
        self.assertEqual(enq_row["email"], "master_test_enquiry@smrmotors.com")

        # Admin replies to enquiry
        reply_payload = {"reply_message": "Yes, you can visit our Salem showroom anytime today."}
        rep_res = self.client.post(f"/api/admin/enquiries/{enq_id}/reply", json=reply_payload, headers=self.admin_headers)
        self.assertEqual(rep_res.status_code, 200)

        # Verify reply in TiDB enquiry_replies table
        fresh_conn = get_db()
        cursor = fresh_conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM enquiry_replies WHERE enquiry_id = %s", (enq_id,))
        rep_row = cursor.fetchone()
        cursor.execute("SELECT admin_reply FROM enquiries WHERE id = %s", (enq_id,))
        updated_enq = cursor.fetchone()
        cursor.close()
        fresh_conn.close()

        self.assertIsNotNone(rep_row)
        self.assertIn("Salem showroom", rep_row["reply_message"])
        self.assertIn("Salem showroom", updated_enq["admin_reply"])

    # =========================================================================
    # SCENARIO 11: Real-Time User & Admin Chat Persistence
    # =========================================================================
    def test_11_chat_system_persistence(self):
        """Scenario 11: User-Admin chat conversations and messages survive restarts in TiDB."""
        # Use existing user id 1
        user_token = jwt.encode(
            {"id": 1, "email": "rider@smrmotors.com", "name": "Chat Master", "role": "user", "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)},
            JWT_SECRET,
            algorithm="HS256"
        )
        user_headers = {"Authorization": f"Bearer {user_token}", "Content-Type": "application/json"}

        create_res = self.client.post("/api/chat/conversations", json={
            "subject": "Discount Enquiry on Master Bike",
            "message": "Hello SMR Team, is there any room for price negotiation?"
        }, headers=user_headers)
        self.assertEqual(create_res.status_code, 201)
        res_data = create_res.get_json()
        conv_id = res_data.get("conversation_id") or (res_data.get("conversation", {}).get("id"))
        self.assertIsNotNone(conv_id)

        admin_reply_res = self.client.post(f"/api/chat/conversations/{conv_id}/messages", json={
            "message": "Hello! Yes, we can offer a ₹5,000 seasonal discount if purchased this week."
        }, headers=self.admin_headers)
        self.assertEqual(admin_reply_res.status_code, 201)

        # Verify in TiDB directly on fresh connection
        fresh_conn = get_db()
        cursor = fresh_conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM chat_conversations WHERE id = %s", (conv_id,))
        conv_row = cursor.fetchone()
        cursor.execute("SELECT * FROM chat_messages WHERE conversation_id = %s ORDER BY id ASC", (conv_id,))
        messages = cursor.fetchall()
        cursor.close()
        fresh_conn.close()

        self.assertIsNotNone(conv_row)
        self.assertGreaterEqual(len(messages), 2)

    # =========================================================================
    # SCENARIO 12: Role-Based Access Control & Financial Privacy
    # =========================================================================
    def test_12_role_based_security_and_financial_privacy(self):
        """Scenario 12: Strict separation between User, Admin, and Superadmin."""
        user_token = jwt.encode(
            {"id": 1, "email": "regular@smrmotors.com", "name": "Regular User", "role": "user", "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)},
            JWT_SECRET,
            algorithm="HS256"
        )
        user_headers = {"Authorization": f"Bearer {user_token}", "Content-Type": "application/json"}

        # Regular user blocked from admin dashboard
        admin_api_res = self.client.get("/api/admin/dashboard", headers=user_headers)
        self.assertIn(admin_api_res.status_code, (401, 403))

        # Regular user cannot see financial details in public bike listings
        pub_bike_res = self.client.get("/api/bikes")
        bikes = pub_bike_res.get_json().get("bikes") or []
        if bikes:
            first = bikes[0]
            self.assertIsNone(first.get("buying_price"))
            self.assertIsNone(first.get("profit"))
            self.assertIsNone(first.get("expenses"))

        # Standard admin cannot access superadmin staff management
        staff_res = self.client.get("/api/admin/staff", headers=self.admin_headers)
        self.assertEqual(staff_res.status_code, 403)

        # Superadmin can access staff management
        super_staff_res = self.client.get("/api/admin/staff", headers=self.superadmin_headers)
        self.assertEqual(super_staff_res.status_code, 200)

    # =========================================================================
    # SCENARIO 13: Durable Image Persistence Across Ephemeral Disk Resets
    # =========================================================================
    def test_13_durable_image_persistence(self):
        """Scenario 13: Bike image saved to TiDB durable_images; survives local disk deletion."""
        test_filename = f"master_test_bike_{int(time.time())}.jpg"
        dummy_image_data = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xFF\xDB\x00C\x00" + b"TEST_IMAGE_BYTES_12345"

        # 1. Save directly into TiDB Cloud durable_images table
        persisted = save_durable_image(test_filename, dummy_image_data, mime_type="image/jpeg")
        self.assertTrue(persisted, "Failed to persist image to TiDB durable_images table!")

        # 2. Verify image row exists in TiDB on fresh connection
        fresh_conn = get_db()
        cursor = fresh_conn.cursor(dictionary=True)
        cursor.execute("SELECT filename, mime_type, file_size FROM durable_images WHERE filename = %s", (test_filename,))
        row = cursor.fetchone()
        cursor.close()
        fresh_conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row["filename"], test_filename)

        # 3. Simulate Render redeployment / disk wipe: Ensure file does NOT exist on local disk
        local_disk_path = os.path.join(UPLOAD_DIR, test_filename)
        if os.path.exists(local_disk_path):
            os.remove(local_disk_path)
        self.assertFalse(os.path.exists(local_disk_path), "File should not exist on disk prior to pull")

        # 4. Request the image via HTTP /uploads/<filename>
        # The backend should detect missing disk file, fetch binary from TiDB, re-cache on disk, and serve
        serve_res = self.client.get(f"/uploads/{test_filename}")
        self.assertEqual(serve_res.status_code, 200)
        self.assertEqual(serve_res.data, dummy_image_data)
        self.assertEqual(serve_res.content_type, "image/jpeg")

        # 5. Verify it was re-cached on disk for fast future reads
        self.assertTrue(os.path.exists(local_disk_path), "File should now be re-cached on disk after TiDB retrieval")


if __name__ == "__main__":
    unittest.main()
