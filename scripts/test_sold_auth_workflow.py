import sys
import os
import unittest
import datetime
import jwt
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.getcwd(), "my-node-app"))

from app import app, JWT_SECRET

class TestSoldAuthWorkflow(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        app.config["TESTING"] = True

        # Valid Admin Token
        admin_payload = {
            "id": 2,
            "username": "staff_admin",
            "role": "admin",
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)
        }
        self.admin_token = jwt.encode(admin_payload, JWT_SECRET, algorithm="HS256")

        # Valid Superadmin Token
        super_payload = {
            "id": 1,
            "username": "owner_admin",
            "role": "superadmin",
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)
        }
        self.superadmin_token = jwt.encode(super_payload, JWT_SECRET, algorithm="HS256")

        # Expired Token
        expired_payload = {
            "id": 1,
            "username": "expired_admin",
            "role": "admin",
            "exp": datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)
        }
        self.expired_token = jwt.encode(expired_payload, JWT_SECRET, algorithm="HS256")

        # Normal User Token
        user_payload = {
            "id": 99,
            "username": "normal_user",
            "role": "user",
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)
        }
        self.user_token = jwt.encode(user_payload, JWT_SECRET, algorithm="HS256")

        self.valid_sale_data = {
            "customer_name": "Karthik Raja",
            "customer_phone": "9876543210",
            "customer_city": "Madurai",
            "customer_location": "Anna Nagar",
            "customer_state": "Tamil Nadu",
            "actual_sale_price": "85000",
            "sale_date": "2026-11-06",
            "payment_method": "UPI",
            "payment_status": "Full Payment",
            "advance_amount": "85000",
            "remaining_amount": "0",
            "notes": "Full payment received via GPay"
        }

    def test_missing_auth_header(self):
        resp = self.client.post("/api/admin/bikes/1001/sold", data=self.valid_sale_data)
        self.assertEqual(resp.status_code, 401)
        data = resp.get_json()
        self.assertFalse(data["success"])
        self.assertIn("Missing admin authorization header", data["message"])

    def test_bearer_undefined_token(self):
        headers = {"Authorization": "Bearer undefined"}
        resp = self.client.post("/api/admin/bikes/1001/sold", data=self.valid_sale_data, headers=headers)
        self.assertEqual(resp.status_code, 401)
        data = resp.get_json()
        self.assertFalse(data["success"])
        self.assertIn("missing or invalid", data["message"])

    def test_bearer_null_token(self):
        headers = {"Authorization": "Bearer null"}
        resp = self.client.post("/api/admin/bikes/1001/sold", data=self.valid_sale_data, headers=headers)
        self.assertEqual(resp.status_code, 401)
        data = resp.get_json()
        self.assertFalse(data["success"])
        self.assertIn("missing or invalid", data["message"])

    def test_expired_token(self):
        headers = {"Authorization": f"Bearer {self.expired_token}"}
        resp = self.client.post("/api/admin/bikes/1001/sold", data=self.valid_sale_data, headers=headers)
        self.assertEqual(resp.status_code, 401)
        data = resp.get_json()
        self.assertFalse(data["success"])
        self.assertIn("expired", data["message"].lower())

    def test_unauthorized_user_role(self):
        headers = {"Authorization": f"Bearer {self.user_token}"}
        resp = self.client.post("/api/admin/bikes/1001/sold", data=self.valid_sale_data, headers=headers)
        self.assertEqual(resp.status_code, 403)
        data = resp.get_json()
        self.assertFalse(data["success"])
        self.assertIn("Administrative privileges required", data["message"])

    @patch("app.get_db")
    def test_valid_admin_token_finalizes_sale_successfully(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 101
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Bike record exists and is approved (not sold)
        bike_db_record = {
            "id": 1001,
            "title": "Yamaha FZ-S V3",
            "brand": "Yamaha",
            "model": "FZ-S",
            "price": 89000,
            "status": "approved",
            "listing_status": "accepted",
            "isSoldout": 0,
            "buying_price": 70000,
            "expenses": 2000,
            "seller_id": 5
        }

        # Verification query returns status="sold"
        verified_record = {
            "id": 1001,
            "status": "sold",
            "listing_status": "soldout",
            "isSoldout": 1,
            "sold_at": "2026-11-06",
            "sold_by": "staff_admin"
        }

        mock_cursor.fetchone.side_effect = [
            bike_db_record,
            verified_record
        ]

        executed_queries = []
        def track_execute(query, params=None):
            executed_queries.append((query, params))
        mock_cursor.execute.side_effect = track_execute

        headers = {"Authorization": f"Bearer {self.admin_token}"}
        resp = self.client.post("/api/admin/bikes/1001/sold", data=self.valid_sale_data, headers=headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertIn("sale completed successfully", data["message"].lower())
        self.assertEqual(data["transaction"]["bike_id"], 1001)
        self.assertEqual(data["transaction"]["customer_name"], "Karthik Raja")
        self.assertEqual(data["transaction"]["actual_sale_price"], 85000.0)

        # Confirm commit was executed
        mock_conn.commit.assert_called()

        # Confirm UPDATE bikes SET isSoldout = 1 was called
        update_bikes = [q for q, p in executed_queries if "UPDATE bikes SET" in q and "isSoldout = 1" in q]
        self.assertTrue(len(update_bikes) > 0, "UPDATE bikes SET isSoldout = 1 was not called!")

    @patch("app.get_db")
    def test_superadmin_token_saves_financial_details(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 102
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        bike_db_record = {
            "id": 1002,
            "title": "KTM Duke 250",
            "brand": "KTM",
            "model": "Duke 250",
            "price": 180000,
            "status": "approved",
            "listing_status": "accepted",
            "isSoldout": 0,
            "buying_price": 140000,
            "expenses": 5000,
            "seller_id": 8
        }

        verified_record = {
            "id": 1002,
            "status": "sold",
            "listing_status": "soldout",
            "isSoldout": 1,
            "sold_at": "2026-11-06",
            "sold_by": "owner_admin"
        }

        mock_cursor.fetchone.side_effect = [
            bike_db_record,
            verified_record
        ]

        sale_data_with_fin = dict(self.valid_sale_data)
        sale_data_with_fin.update({
            "actual_sale_price": "175000",
            "buying_price": "145000",
            "repair_expense": "3000",
            "other_expense": "2000"
        })

        headers = {"Authorization": f"Bearer {self.superadmin_token}"}
        resp = self.client.post("/api/admin/bikes/1002/sold", data=sale_data_with_fin, headers=headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        # Superadmin response includes financials
        self.assertIn("financials", data["transaction"])
        fin = data["transaction"]["financials"]
        self.assertEqual(fin["buying_price"], 145000.0)
        self.assertEqual(fin["selling_price"], 175000.0)
        self.assertEqual(fin["total_expenses"], 5000.0)
        self.assertEqual(fin["net_profit"], 25000.0) # 175000 - 145000 - 5000 = 25000

    @patch("app.get_db")
    def test_duplicate_sale_prevention(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Bike is already sold
        bike_db_record = {
            "id": 1003,
            "title": "Royal Enfield Classic 350",
            "brand": "Royal Enfield",
            "model": "Classic 350",
            "price": 150000,
            "status": "sold",
            "listing_status": "soldout",
            "isSoldout": 1,
            "buying_price": 120000,
            "seller_id": 9
        }

        mock_cursor.fetchone.return_value = bike_db_record

        headers = {"Authorization": f"Bearer {self.admin_token}"}
        resp = self.client.post("/api/admin/bikes/1003/sold", data=self.valid_sale_data, headers=headers)
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertFalse(data["success"])
        self.assertIn("already marked as sold", data["message"].lower())

if __name__ == "__main__":
    unittest.main()
