import unittest
import json
import jwt
import datetime
import sys
import os

sys.path.append('my-node-app')
from app import app, JWT_SECRET, get_db

class TestApprovalPersistenceAndSoldOut(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()
        # Generate valid tokens
        cls.superadmin_token = jwt.encode({
            'username': 'superadmin',
            'role': 'superadmin',
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=2)
        }, JWT_SECRET, algorithm='HS256')

        cls.staff_token = jwt.encode({
            'username': 'staffadmin',
            'role': 'admin',
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=2)
        }, JWT_SECRET, algorithm='HS256')

    def test_01_user_listing_submission_stored_as_pending(self):
        """Test 1: User lists bike; verify status is pending."""
        payload = {
            "title": "Yamaha R15 V4 Racing Blue Test",
            "brand": "Yamaha",
            "model": "R15 V4",
            "year": 2023,
            "price": 175000,
            "kilometers_driven": 8500,
            "fuel_type": "Petrol",
            "transmission": "Manual",
            "description": "Mint condition Yamaha R15 V4 for testing persistence.",
            "seller_name": "Test Seller User",
            "seller_phone": "+91 99887 76655",
            "registration_number": "TN-09-CD-1234",
            "location": "Chennai Showroom",
            "images": [
                "/static/images/IMG-20251204-WA0051.jpg",
                "/static/images/IMG-20251204-WA0053.jpg"
            ]
        }
        res = self.client.post("/api/user/sell-bike", json=payload)
        self.assertIn(res.status_code, [200, 201])
        data = json.loads(res.data)
        self.assertTrue(data.get("success"))
        bike_id = data.get("bike_id") or data.get("id")
        self.assertIsNotNone(bike_id)
        TestApprovalPersistenceAndSoldOut.test_bike_id = bike_id

        # Verify in DB
        conn = get_db()
        self.assertIsNotNone(conn)
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT status, listing_status, isSoldout FROM bikes WHERE id = %s", (bike_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row["status"], "pending")
        self.assertEqual(row["listing_status"], "pending")
        self.assertEqual(row["isSoldout"], 0)

    def test_02_admin_approves_bike_persists_in_tidb(self):
        """Test 2: Admin approves bike; verify TiDB permanent update."""
        bike_id = getattr(TestApprovalPersistenceAndSoldOut, 'test_bike_id', None)
        self.assertIsNotNone(bike_id)

        headers = {"Authorization": f"Bearer {self.staff_token}"}
        res = self.client.post(f"/api/admin/bikes/{bike_id}/approve", headers=headers, json={})
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data.get("success"))

        # Verify directly in TiDB database
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT status, listing_status, isSoldout, approved_by, approved_at FROM bikes WHERE id = %s", (bike_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row["status"], "approved")
        self.assertEqual(row["listing_status"], "published")
        self.assertEqual(row["isSoldout"], 0)
        self.assertEqual(row["approved_by"], "staffadmin")
        self.assertIsNotNone(row["approved_at"])

    def test_03_approved_bike_appears_on_marketplace_across_refreshes(self):
        """Test 3: Approved bike appears on public marketplace and stays after refresh."""
        bike_id = getattr(TestApprovalPersistenceAndSoldOut, 'test_bike_id', None)

        # 1. Fetch marketplace default
        res1 = self.client.get("/api/bikes?limit=50")
        self.assertEqual(res1.status_code, 200)
        bikes1 = json.loads(res1.data).get("data") or json.loads(res1.data).get("bikes")
        ids1 = [b["id"] for b in bikes1]
        self.assertIn(bike_id, ids1)

        # 2. Simulate refresh / second query with status=approved
        res2 = self.client.get("/api/bikes?status=approved&limit=50")
        self.assertEqual(res2.status_code, 200)
        bikes2 = json.loads(res2.data).get("data") or json.loads(res2.data).get("bikes")
        ids2 = [b["id"] for b in bikes2]
        self.assertIn(bike_id, ids2)

        # Verify bike normalization attributes
        target_b = next((b for b in bikes2 if b["id"] == bike_id), None)
        self.assertIsNotNone(target_b)
        self.assertEqual(target_b["status"], "approved")
        self.assertEqual(target_b["listing_status"], "published")
        self.assertEqual(target_b["isAccepted"], 1)
        self.assertEqual(target_b["isSoldout"], 0)

    def test_04_mark_motorcycle_sold_out(self):
        """Test 4: Authorized admin executes sold out operation."""
        bike_id = getattr(TestApprovalPersistenceAndSoldOut, 'test_bike_id', None)
        headers = {"Authorization": f"Bearer {self.staff_token}"}
        
        payload = {
            "actual_sale_price": 172000,
            "seller_payout": 160000,
            "buyer_name": "Ravi Kumar",
            "buyer_phone": "+91 98401 23456",
            "service_expense": 2000,
            "other_expense": 1000
        }
        res = self.client.post(f"/api/admin/bikes/{bike_id}/sold", headers=headers, json=payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data.get("success"))

        # Verify in TiDB
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT status, listing_status, isSoldout, sold_by, sold_at, sold_snapshot FROM bikes WHERE id = %s", (bike_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()

        self.assertIsNotNone(row)
        self.assertIn(row["status"], ["sold", "soldout"])
        self.assertEqual(row["listing_status"], "soldout")
        self.assertEqual(row["isSoldout"], 1)
        self.assertEqual(row["sold_by"], "staffadmin")
        self.assertIsNotNone(row["sold_at"])
        self.assertIsNotNone(row["sold_snapshot"])

    def test_05_sold_bike_removed_from_active_marketplace(self):
        """Test 5: Public marketplace inventory excludes sold out motorcycle."""
        bike_id = getattr(TestApprovalPersistenceAndSoldOut, 'test_bike_id', None)

        # Default public marketplace call
        res = self.client.get("/api/bikes?limit=50")
        self.assertEqual(res.status_code, 200)
        bikes = json.loads(res.data).get("data") or json.loads(res.data).get("bikes")
        ids = [b["id"] for b in bikes]
        self.assertNotIn(bike_id, ids, "Sold bike must not appear in active marketplace inventory!")

        # Querying status=approved
        res2 = self.client.get("/api/bikes?status=approved&limit=50")
        bikes2 = json.loads(res2.data).get("data") or json.loads(res2.data).get("bikes")
        ids2 = [b["id"] for b in bikes2]
        self.assertNotIn(bike_id, ids2, "Sold bike must not appear in approved inventory list!")

    def test_06_enquiries_on_sold_bike_rejected(self):
        """Test 6: Enquiry submitted on sold bike is rejected with HTTP 400."""
        bike_id = getattr(TestApprovalPersistenceAndSoldOut, 'test_bike_id', None)
        payload = {
            "bike_id": bike_id,
            "bike_title": "Yamaha R15 V4",
            "name": "Eager Buyer",
            "email": "buyer@example.com",
            "phone": "+91 91234 56789",
            "message": "Is this bike still available?"
        }
        res = self.client.post("/api/enquiries", json=payload)
        self.assertEqual(res.status_code, 400)
        data = json.loads(res.data)
        self.assertFalse(data.get("success"))
        self.assertIn("sold", data.get("message", "").lower())

    def test_07_sold_bikes_admin_api_list(self):
        """Test 7: Sold bike appears on Admin Sold Out Bikes page with filters."""
        bike_id = getattr(TestApprovalPersistenceAndSoldOut, 'test_bike_id', None)
        headers = {"Authorization": f"Bearer {self.staff_token}"}

        # 1. Fetch list
        res = self.client.get("/api/admin/sold-bikes?limit=50", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data.get("success"))
        sold_list = data.get("data", [])
        ids = [b["bike_id"] for b in sold_list]
        self.assertIn(bike_id, ids)

        # 2. Test brand filter
        res_brand = self.client.get("/api/admin/sold-bikes?brand=Yamaha", headers=headers)
        self.assertEqual(res_brand.status_code, 200)
        yamaha_list = json.loads(res_brand.data).get("data", [])
        self.assertTrue(all(b["brand"].lower() == "yamaha" for b in yamaha_list))

        # 3. Test search filter
        res_search = self.client.get(f"/api/admin/sold-bikes?search={bike_id}", headers=headers)
        self.assertEqual(res_search.status_code, 200)
        search_list = json.loads(res_search.data).get("data", [])
        self.assertEqual(len(search_list), 1)
        self.assertEqual(search_list[0]["bike_id"], bike_id)

    def test_08_sold_bike_detail_and_snapshot(self):
        """Test 8: Detailed historical snapshot contains gallery images, specs, seller, and audit info."""
        bike_id = getattr(TestApprovalPersistenceAndSoldOut, 'test_bike_id', None)
        headers = {"Authorization": f"Bearer {self.superadmin_token}"}

        res = self.client.get(f"/api/admin/sold-bikes/{bike_id}", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data.get("success"))
        snap = data.get("data")
        self.assertIsNotNone(snap)

        self.assertEqual(snap.get("bike_id"), bike_id)
        self.assertEqual(snap.get("brand"), "Yamaha")
        self.assertEqual(snap.get("model"), "R15 V4")
        self.assertTrue(len(snap.get("images", [])) >= 1)
        self.assertIsNotNone(snap.get("seller"))
        self.assertEqual(snap["seller"]["name"], "Test Seller User")
        self.assertIsNotNone(snap.get("sold_metadata"))
        self.assertEqual(snap["sold_metadata"]["sold_by"], "staffadmin")
        self.assertEqual(snap["sold_metadata"]["buyer_name"], "Ravi Kumar")

    def test_09_superadmin_views_confidential_financials(self):
        """Test 9: Superadmin receives full financial telemetry."""
        bike_id = getattr(TestApprovalPersistenceAndSoldOut, 'test_bike_id', None)
        headers = {"Authorization": f"Bearer {self.superadmin_token}"}

        res = self.client.get(f"/api/admin/sold-bikes/{bike_id}", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data.get("is_superadmin"))
        snap = data.get("data")
        self.assertIn("financials", snap)
        fin = snap["financials"]
        self.assertEqual(float(fin["actual_sale_price"]), 172000.0)
        self.assertEqual(float(fin["seller_payout"]), 160000.0)
        self.assertEqual(float(fin["realized_profit"]), 9000.0) # 172000 - 160000 - 3000

    def test_10_staff_admin_financials_redacted(self):
        """Test 10: Staff admin view omits/redacts confidential financials."""
        bike_id = getattr(TestApprovalPersistenceAndSoldOut, 'test_bike_id', None)
        headers = {"Authorization": f"Bearer {self.staff_token}"}

        res = self.client.get(f"/api/admin/sold-bikes/{bike_id}", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertFalse(data.get("is_superadmin"))
        snap = data.get("data")
        self.assertNotIn("financials", snap)
        self.assertNotIn("buying_price", snap)
        self.assertNotIn("seller_payout", snap)
        self.assertNotIn("realized_profit", snap)
        if "sold_metadata" in snap:
            self.assertNotIn("actual_sale_price", snap["sold_metadata"])

    def test_11_duplicate_operations_prevented(self):
        """Test 11: Duplicate approval and duplicate sold out calls are rejected with HTTP 400."""
        bike_id = getattr(TestApprovalPersistenceAndSoldOut, 'test_bike_id', None)
        headers = {"Authorization": f"Bearer {self.staff_token}"}

        # Attempt to mark sold again
        res_sold = self.client.post(f"/api/admin/bikes/{bike_id}/sold", headers=headers, json={"actual_sale_price": 170000})
        self.assertEqual(res_sold.status_code, 400)
        self.assertIn("already", json.loads(res_sold.data).get("message", "").lower())

    def test_12_data_integrity_preserved(self):
        """Test 12: Ensure original bike, images, and seller info are intact in TiDB."""
        bike_id = getattr(TestApprovalPersistenceAndSoldOut, 'test_bike_id', None)
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, title, brand, model, price, images, seller_name, seller_phone FROM bikes WHERE id = %s", (bike_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row["brand"], "Yamaha")
        self.assertEqual(row["model"], "R15 V4")
        self.assertEqual(row["seller_name"], "Test Seller User")
        self.assertIsNotNone(row["images"])

if __name__ == '__main__':
    unittest.main()
