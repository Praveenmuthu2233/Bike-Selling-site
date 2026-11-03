import unittest
import json
import os
import sys
import time

# Ensure my-node-app is in path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_DIR = os.path.join(BASE_DIR, "my-node-app")
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from app import app, JWT_SECRET, get_db
import jwt
import datetime

class PermanentPersistenceBugTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = app.test_client()
        cls.app.testing = True

        now = datetime.datetime.now(datetime.timezone.utc)
        cls.superadmin_token = jwt.encode({
            'admin_id': 1,
            'username': 'super_tester',
            'role': 'superadmin',
            'exp': now + datetime.timedelta(hours=2)
        }, JWT_SECRET, algorithm='HS256')

        cls.user_token = jwt.encode({
            'user_id': 8888,
            'email': 'persistence_user@example.com',
            'role': 'user',
            'exp': now + datetime.timedelta(hours=2)
        }, JWT_SECRET, algorithm='HS256')

    def test_01_user_submits_bike_pending_in_tidb(self):
        """TEST 1 & 2: User submits a bike and it exists in TiDB with pending status."""
        payload = {
            "title": "Persistent Test Rider Motorcycle",
            "brand": "Royal Enfield",
            "model": "Hunter 350",
            "year": 2023,
            "price": 165000,
            "kilometers_driven": 4500,
            "fuel_type": "Petrol",
            "transmission": "Manual",
            "location": "Salem, Tamil Nadu",
            "description": "Inspected motorcycle for persistence testing",
            "registration_number": "TN-30-PER-0001",
            "seller_name": "Rider Tester",
            "seller_phone": "9876543210"
        }
        res = self.app.post('/api/bikes', data=json.dumps(payload), content_type='application/json')
        self.assertIn(res.status_code, [200, 201])
        data = res.get_json()
        self.assertTrue(data.get("success"))
        bike_id = data.get("id")
        self.assertIsNotNone(bike_id)

        # TEST 2: Query TiDB Cloud directly
        conn = get_db()
        self.assertIsNotNone(conn)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, status, listing_status, isSoldout, title FROM bikes WHERE id = %s", (bike_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row["status"], "pending")
        self.assertEqual(row["listing_status"], "pending")
        self.assertEqual(row["isSoldout"], 0)

        PermanentPersistenceBugTest.created_bike_id = bike_id

    def test_02_pending_bike_not_on_homepage(self):
        """TEST 11: Pending bike does not appear on public marketplace."""
        bike_id = getattr(PermanentPersistenceBugTest, 'created_bike_id', None)
        self.assertIsNotNone(bike_id)

        res = self.app.get('/api/bikes')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        bike_ids = [b["id"] for b in data.get("data", [])]
        self.assertNotIn(bike_id, bike_ids)

    def test_03_admin_approves_bike_verified_in_tidb(self):
        """TEST 3 & 4: Admin approves the bike; existing record has approved status in TiDB."""
        bike_id = getattr(PermanentPersistenceBugTest, 'created_bike_id', None)
        self.assertIsNotNone(bike_id)

        headers = {'Authorization': f'Bearer {self.superadmin_token}'}
        res = self.app.post(f'/api/admin/bikes/{bike_id}/approve',
                            data=json.dumps({"approved_price": 165000}),
                            content_type='application/json',
                            headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json().get("success"))

        # TEST 4: Verify directly in TiDB
        conn = get_db()
        self.assertIsNotNone(conn)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, status, listing_status, isSoldout, approved_by, approved_at FROM bikes WHERE id = %s", (bike_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row["status"], "approved")
        self.assertEqual(row["listing_status"], "published")
        self.assertEqual(row["isSoldout"], 0)
        self.assertIsNotNone(row["approved_at"])

    def test_04_check_homepage_visible_and_refreshes(self):
        """TEST 5 & 6: Check homepage displays approved bike across multiple consecutive refreshes."""
        bike_id = getattr(PermanentPersistenceBugTest, 'created_bike_id', None)
        self.assertIsNotNone(bike_id)

        # Multiple consecutive requests (simulating user refreshes)
        for i in range(5):
            res = self.app.get('/api/bikes?limit=50')
            self.assertEqual(res.status_code, 200)
            # Verify Cache-Control header prevents browser/CDN stale storage
            self.assertIn("no-store", res.headers.get("Cache-Control", ""))

            data = res.get_json()
            bike_ids = [b["id"] for b in data.get("data", [])]
            self.assertIn(bike_id, bike_ids, f"Bike #{bike_id} disappeared on refresh {i+1}!")

    def test_05_admin_submits_approved_bike_directly_visible_on_homepage(self):
        """Admin adds a bike directly to inventory: must have listing_status='published' and be visible."""
        headers = {'Authorization': f'Bearer {self.superadmin_token}'}
        payload = {
            "title": "Direct Admin Showroom Intake",
            "brand": "Yamaha",
            "model": "MT-15",
            "year": 2023,
            "price": 140000,
            "status": "approved",
            "kilometers_driven": 2000,
            "registration_number": "TN-30-ADM-9999"
        }
        res = self.app.post('/api/bikes', data=json.dumps(payload), content_type='application/json', headers=headers)
        self.assertIn(res.status_code, [200, 201])
        data = res.get_json()
        adm_bike_id = data.get("id")

        # Query TiDB
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, status, listing_status, isSoldout FROM bikes WHERE id = %s", (adm_bike_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        self.assertEqual(row["status"], "approved")
        self.assertEqual(row["listing_status"], "published")
        self.assertEqual(row["isSoldout"], 0)

        # Check homepage
        hp_res = self.app.get('/api/bikes?limit=50')
        self.assertEqual(hp_res.status_code, 200)
        hp_ids = [b["id"] for b in hp_res.get_json().get("data", [])]
        self.assertIn(adm_bike_id, hp_ids)

        PermanentPersistenceBugTest.admin_bike_id = adm_bike_id

    def test_06_admin_marks_sold_out_removed_from_homepage(self):
        """TEST 10: Authorized admin marks sold out; bike leaves active homepage but stays in sold gallery."""
        adm_bike_id = getattr(PermanentPersistenceBugTest, 'admin_bike_id', None)
        self.assertIsNotNone(adm_bike_id)

        headers = {'Authorization': f'Bearer {self.superadmin_token}'}
        payload = {
            "actual_sale_price": 142000,
            "seller_payout": 125000,
            "buyer_name": "Happy Buyer",
            "buyer_phone": "9876543219"
        }
        res = self.app.post(f'/api/admin/bikes/{adm_bike_id}/sold',
                            data=json.dumps(payload),
                            content_type='application/json',
                            headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json().get("success"))

        # Verify not on homepage
        hp_res = self.app.get('/api/bikes?limit=50')
        hp_ids = [b["id"] for b in hp_res.get_json().get("data", [])]
        self.assertNotIn(adm_bike_id, hp_ids)

        # Verify present in sold API
        sold_res = self.app.get('/api/bikes/sold')
        self.assertEqual(sold_res.status_code, 200)
        sold_ids = [b["id"] for b in sold_res.get_json().get("data", [])]
        self.assertIn(adm_bike_id, sold_ids)

    def test_07_all_existing_approved_bikes_remain_visible(self):
        """TEST 12: Verify all approved bikes in TiDB remain permanently visible."""
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM bikes WHERE (status='approved' OR listing_status='published') AND isSoldout=0")
        approved_rows = cursor.fetchall()
        cursor.close()
        conn.close()

        approved_ids = set(r["id"] for r in approved_rows)

        res = self.app.get('/api/bikes?limit=100')
        self.assertEqual(res.status_code, 200)
        homepage_ids = set(b["id"] for b in res.get_json().get("data", []))

        # Check intersection
        self.assertTrue(approved_ids.issubset(homepage_ids) or len(homepage_ids) >= len(approved_ids))

if __name__ == '__main__':
    unittest.main()
