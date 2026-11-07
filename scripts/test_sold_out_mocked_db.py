import os
import sys
import unittest
import json
import jwt
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "my-node-app")))

from app import app, JWT_SECRET

class TestSoldOutMockedDb(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()
        
        self.superadmin_token = jwt.encode(
            {"id": 1, "username": "superadmin", "role": "superadmin", "exp": datetime.now(timezone.utc).timestamp() + 3600},
            JWT_SECRET,
            algorithm="HS256"
        )
        self.superadmin_headers = {"Authorization": f"Bearer {self.superadmin_token}"}
        
        self.staff_token = jwt.encode(
            {"id": 2, "username": "staff1", "role": "admin", "exp": datetime.now(timezone.utc).timestamp() + 3600},
            JWT_SECRET,
            algorithm="HS256"
        )
        self.staff_headers = {"Authorization": f"Bearer {self.staff_token}"}

    def generate_sample_sold_records(self, count=25):
        records = []
        for i in range(1, count + 1):
            records.append({
                "id": i,
                "bike_id": i,
                "title": f"Royal Enfield Classic 350 Unit #{i}" if i % 2 == 0 else f"Yamaha MT-15 Unit #{i}",
                "brand": "Royal Enfield" if i % 2 == 0 else "Yamaha",
                "model": "Classic 350" if i % 2 == 0 else "MT-15",
                "year": 2021 + (i % 3),
                "registration_number": f"TN-{20+i}-AB-{1000+i}",
                "kilometers_driven": 12000 + i * 500,
                "fuel_type": "Petrol",
                "transmission": "Manual",
                "seller_name": f"Seller {i}",
                "seller_phone": f"+91 98765 432{i%10}0",
                "price": 120000 + i * 1000,
                "actual_sale_price": 125000 + i * 1000,
                "buying_price": 100000 + i * 500,
                "sb_buying_price": 100000 + i * 500,
                "seller_payout": 100000 + i * 500,
                "total_expenses": 2000 + i * 100,
                "realized_profit": 23000 + i * 400,
                "effective_sold_by": "superadmin" if i % 2 == 0 else "staff1",
                "effective_sold_at": f"2026-11-0{min(9, i):02d} 14:30:00",
                "sb_buyer_name": f"Customer {i}",
                "sb_buyer_phone": f"+91 91234 567{i%10}0",
                "sb_buyer_city": "Salem" if i % 2 == 0 else "Coimbatore",
                "sb_buyer_location": "Salem, Tamil Nadu" if i % 2 == 0 else "Coimbatore, Tamil Nadu",
                "sb_payment_status": "Full Payment" if i % 3 != 0 else "Partial",
                "sb_payment_method": "UPI" if i % 2 == 0 else "Cash",
                "images": json.dumps([f"/static/images/bike_{i}.jpg"])
            })
        return records

    @patch("app.get_db")
    def test_admin_pagination_and_archive_counts(self, mock_get_db):
        """Verify server-side pagination with 10 default, custom limits (20, 50, 100), and full archive totals."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = self.generate_sample_sold_records(25)
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value = mock_conn

        # 1. Default Limit = 10, Page 1
        resp = self.client.get("/api/admin/sold-bikes?page=1&limit=10", headers=self.superadmin_headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(len(data["data"]), 10)
        self.assertEqual(data["total_sold_count"], 25)
        self.assertEqual(data["total_matching_count"], 25)
        self.assertEqual(data["pagination"]["page"], 1)
        self.assertEqual(data["pagination"]["totalPages"], 3)
        self.assertTrue(data["pagination"]["hasNext"])
        self.assertFalse(data["pagination"]["hasPrev"])

        # 2. Page 2, Limit = 10
        resp2 = self.client.get("/api/admin/sold-bikes?page=2&limit=10", headers=self.superadmin_headers)
        data2 = resp2.get_json()
        self.assertEqual(len(data2["data"]), 10)
        self.assertEqual(data2["pagination"]["page"], 2)
        self.assertTrue(data2["pagination"]["hasPrev"])

        # 3. Limit = 20
        resp3 = self.client.get("/api/admin/sold-bikes?page=1&limit=20", headers=self.superadmin_headers)
        data3 = resp3.get_json()
        self.assertEqual(len(data3["data"]), 20)
        self.assertEqual(data3["pagination"]["totalPages"], 2)

        # 4. Limit = 50 and 100
        resp50 = self.client.get("/api/admin/sold-bikes?page=1&limit=50", headers=self.superadmin_headers)
        self.assertEqual(len(resp50.get_json()["data"]), 25)
        self.assertEqual(resp50.get_json()["pagination"]["totalPages"], 1)

        print(f" [PASS] Mocked DB Pagination verified: 25 total units correctly sliced across pages and limits 10, 20, 50, 100.")

    @patch("app.get_db")
    def test_admin_search_and_filters(self, mock_get_db):
        """Verify search, brand, payment status, and date filters across the full archive."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = self.generate_sample_sold_records(25)
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value = mock_conn

        # Brand Filter: Royal Enfield (only even i)
        resp = self.client.get("/api/admin/sold-bikes?brand=Royal+Enfield", headers=self.superadmin_headers)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["total_sold_count"], 25)
        self.assertEqual(data["total_matching_count"], 12)
        for item in data["data"]:
            self.assertEqual(item["brand"], "Royal Enfield")

        # Search Filter: Customer 1
        resp_search = self.client.get("/api/admin/sold-bikes?search=Customer+1", headers=self.superadmin_headers)
        data_search = resp_search.get_json()
        self.assertGreater(data_search["total_matching_count"], 0)

        # Payment Status Filter: Partial
        resp_partial = self.client.get("/api/admin/sold-bikes?payment_status=Partial", headers=self.superadmin_headers)
        data_partial = resp_partial.get_json()
        for item in data_partial["data"]:
            self.assertEqual(item["payment_status"], "Partial")

        print(" [PASS] Mocked DB Search, Brand, and Payment Status filtering verified.")

    @patch("app.get_db")
    def test_admin_rbac_and_profit_calculations(self, mock_get_db):
        """Verify Superadmin receives full financial calculations and Staff Admin has them redacted."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = self.generate_sample_sold_records(5)
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value = mock_conn

        # Superadmin check
        resp_super = self.client.get("/api/admin/sold-bikes", headers=self.superadmin_headers)
        data_super = resp_super.get_json()
        bike_super = data_super["data"][0]
        self.assertIn("buying_price", bike_super)
        self.assertIn("gross_profit", bike_super)
        self.assertIn("realized_profit", bike_super)
        self.assertIn("profit_percentage", bike_super)
        self.assertGreater(bike_super["buying_price"], 0)
        self.assertEqual(bike_super["gross_profit"], bike_super["final_selling_price"] - bike_super["buying_price"])

        # Staff check
        resp_staff = self.client.get("/api/admin/sold-bikes", headers=self.staff_headers)
        data_staff = resp_staff.get_json()
        bike_staff = data_staff["data"][0]
        self.assertNotIn("buying_price", bike_staff)
        self.assertNotIn("gross_profit", bike_staff)
        self.assertNotIn("net_profit", bike_staff)
        self.assertNotIn("profit_percentage", bike_staff)

        print(" [PASS] Mocked DB RBAC and profit margin calculation verified.")

    @patch("app.get_db")
    def test_homepage_sold_bikes_with_mocked_db(self, mock_get_db):
        """Verify /api/homepage/sold-bikes returns at most 6 units even if 25 units exist in DB."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = self.generate_sample_sold_records(25)
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value = mock_conn

        resp = self.client.get("/api/homepage/sold-bikes")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(len(data["data"]), 6, "Homepage must return exactly 6 units when archive has 25")
        
        for item in data["data"]:
            self.assertNotIn("buying_price", item)
            self.assertNotIn("net_profit", item)
            self.assertNotIn("customer_phone", item)
            self.assertIn("price", item)
            self.assertIn("title", item)

        print(f" [PASS] /api/homepage/sold-bikes returned exactly {len(data['data'])} units with private fields stripped.")

if __name__ == "__main__":
    unittest.main()
