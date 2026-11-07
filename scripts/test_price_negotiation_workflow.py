import sys
import os
import unittest
import datetime
import jwt
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.getcwd(), "my-node-app"))

from app import app, JWT_SECRET

class TestPriceNegotiationWorkflow(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        app.config["TESTING"] = True

        # 1. Admin Token (Superadmin)
        admin_payload = {
            "id": 1,
            "username": "admin",
            "role": "superadmin",
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)
        }
        self.admin_token = jwt.encode(admin_payload, JWT_SECRET, algorithm="HS256")
        self.admin_headers = {
            "Authorization": f"Bearer {self.admin_token}",
            "Content-Type": "application/json"
        }

        # 2. Customer A Token (Bike Owner, id=101)
        user_a_payload = {
            "id": 101,
            "name": "Ramesh Customer",
            "email": "ramesh@example.com",
            "phone": "9876543210",
            "role": "user",
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)
        }
        self.user_a_token = jwt.encode(user_a_payload, JWT_SECRET, algorithm="HS256")
        self.user_a_headers = {
            "Authorization": f"Bearer {self.user_a_token}",
            "Content-Type": "application/json"
        }

        # 3. Customer B Token (Unrelated User, id=202)
        user_b_payload = {
            "id": 202,
            "name": "Suresh Other",
            "email": "suresh@example.com",
            "phone": "9876543299",
            "role": "user",
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)
        }
        self.user_b_token = jwt.encode(user_b_payload, JWT_SECRET, algorithm="HS256")
        self.user_b_headers = {
            "Authorization": f"Bearer {self.user_b_token}",
            "Content-Type": "application/json"
        }

    # -------------------------------------------------------------
    # 1. Admin Counteroffer Price Validation
    # -------------------------------------------------------------
    def test_admin_counteroffer_price_validation(self):
        # Negative / Zero
        resp = self.client.post(
            "/api/admin/bikes/9001/negotiate",
            json={"admin_suggested_price": 0},
            headers=self.admin_headers
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("between ₹1 and ₹10,00,000", resp.get_json()["message"])

        # Exceeds 10,00,000
        resp = self.client.post(
            "/api/admin/bikes/9001/negotiate",
            json={"admin_suggested_price": 1000001},
            headers=self.admin_headers
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("between ₹1 and ₹10,00,000", resp.get_json()["message"])

        # Non-numeric
        resp = self.client.post(
            "/api/admin/bikes/9001/negotiate",
            json={"admin_suggested_price": "invalid"},
            headers=self.admin_headers
        )
        self.assertEqual(resp.status_code, 400)

    # -------------------------------------------------------------
    # 2. Strict Approval Guard: Cannot approve pending/offered bikes
    # -------------------------------------------------------------
    @patch("app.get_db")
    def test_admin_approval_locked_when_negotiation_not_accepted(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Case A: status = pending_negotiation
        mock_cursor.fetchone.return_value = {
            "id": 9001,
            "title": "Yamaha MT-15",
            "brand": "Yamaha",
            "model": "MT-15",
            "price": 120000,
            "requested_price": 120000,
            "status": "pending_negotiation",
            "listing_status": "pending_negotiation",
            "negotiation_status": "pending_negotiation",
            "proposed_seller_payout": None,
            "accepted_seller_payout": None,
            "buying_price": None,
            "seller_id": 101,
            "seller_name": "Ramesh Customer",
            "seller_phone": "9876543210"
        }

        resp = self.client.post("/api/admin/bikes/9001/approve", json={"approved_price": 130000}, headers=self.admin_headers)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Price negotiation is still pending", resp.get_json()["message"])

        # Case B: status = offer_sent
        mock_cursor.fetchone.return_value["negotiation_status"] = "offer_sent"
        mock_cursor.fetchone.return_value["proposed_seller_payout"] = 105000.0

        resp = self.client.post("/api/admin/bikes/9001/approve", json={"approved_price": 130000}, headers=self.admin_headers)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Waiting for customer to accept", resp.get_json()["message"])

        # Case C: status = offer_rejected
        mock_cursor.fetchone.return_value["negotiation_status"] = "offer_rejected"

        resp = self.client.post("/api/admin/bikes/9001/approve", json={"approved_price": 130000}, headers=self.admin_headers)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Customer rejected the last price offer", resp.get_json()["message"])

    # -------------------------------------------------------------
    # 3. Admin Proposes Round 1 Counteroffer
    # -------------------------------------------------------------
    @patch("app.get_db")
    def test_admin_propose_counteroffer_round_1(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Bike exists
        mock_cursor.fetchone.side_effect = [
            # 1. Bike lookup
            {
                "id": 9001,
                "title": "Yamaha MT-15",
                "brand": "Yamaha",
                "model": "MT-15",
                "requested_price": 120000,
                "price": 120000,
                "seller_id": 101,
                "seller_name": "Ramesh Customer",
                "seller_phone": "9876543210"
            },
            # 2. Max counteroffer_number query
            {"max_round": None},
            # 3. Existing open conversation lookup (none, insert new)
            None
        ]
        mock_cursor.lastrowid = 501

        resp = self.client.post(
            "/api/admin/bikes/9001/negotiate",
            json={
                "admin_suggested_price": 100000,
                "message": "After vehicle inspection, we can offer ₹1,00,000 guaranteed payout."
            },
            headers=self.admin_headers
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["counteroffer_number"], 1)
        self.assertEqual(data["data"]["proposed_price"], 100000.0)

    # -------------------------------------------------------------
    # 4. RBAC: Only Bike Owner Can Accept / Reject Offer
    # -------------------------------------------------------------
    @patch("app.get_db")
    def test_non_owner_forbidden_from_responding(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchone.return_value = {
            "id": 9001,
            "title": "Yamaha MT-15",
            "seller_id": 101, # owned by Ramesh (101)
            "seller_phone": "9876543210",
            "seller_name": "Ramesh Customer",
            "negotiation_status": "offer_sent"
        }

        # User B (id=202) tries to accept
        resp = self.client.post(
            "/api/users/bikes/9001/negotiate",
            json={"action": "accept"},
            headers=self.user_b_headers
        )
        self.assertEqual(resp.status_code, 403)
        self.assertIn("Unauthorized", resp.get_json()["message"])

    # -------------------------------------------------------------
    # 5. User Declines Round 1 Counteroffer
    # -------------------------------------------------------------
    @patch("app.get_db")
    def test_user_rejects_round_1_counteroffer(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchone.side_effect = [
            # 1. Bike lookup
            {
                "id": 9001,
                "title": "Yamaha MT-15",
                "brand": "Yamaha",
                "model": "MT-15",
                "seller_id": 101,
                "seller_phone": "9876543210",
                "seller_name": "Ramesh Customer",
                "proposed_seller_payout": 100000,
                "negotiation_status": "offer_sent"
            },
            # 2. Active offer lookup
            {
                "id": 501,
                "counteroffer_number": 1,
                "admin_suggested_price": 100000,
                "status": "pending"
            },
            # 3. Existing conversation lookup
            {"id": 77}
        ]

        resp = self.client.post(
            "/api/users/bikes/9001/negotiate",
            json={
                "action": "reject",
                "seller_note": "Expected at least ₹1,10,000 based on recent service and tyres."
            },
            headers=self.user_a_headers
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["negotiation_status"], "offer_rejected")

    # -------------------------------------------------------------
    # 6. Admin Proposes Round 2 Counteroffer (History Preserved)
    # -------------------------------------------------------------
    @patch("app.get_db")
    def test_admin_propose_round_2_counteroffer(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchone.side_effect = [
            # 1. Bike lookup
            {
                "id": 9001,
                "title": "Yamaha MT-15",
                "brand": "Yamaha",
                "model": "MT-15",
                "requested_price": 120000,
                "price": 120000,
                "seller_id": 101,
                "seller_name": "Ramesh Customer",
                "seller_phone": "9876543210"
            },
            # 2. Max counteroffer_number query: previous round was 1
            {"max_round": 1},
            # 3. Existing conversation lookup
            {"id": 77}
        ]

        resp = self.client.post(
            "/api/admin/bikes/9001/negotiate",
            json={
                "admin_suggested_price": 108000,
                "message": "We have reconsidered the recent tyre upgrade and can offer ₹1,08,000."
            },
            headers=self.admin_headers
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["counteroffer_number"], 2)
        self.assertEqual(data["data"]["proposed_price"], 108000.0)

    # -------------------------------------------------------------
    # 7. User Accepts Round 2 Counteroffer -> buying_price Strictly Set
    # -------------------------------------------------------------
    @patch("app.get_db")
    def test_user_accepts_round_2_sets_buying_price(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchone.side_effect = [
            # 1. Bike lookup
            {
                "id": 9001,
                "title": "Yamaha MT-15",
                "brand": "Yamaha",
                "model": "MT-15",
                "seller_id": 101,
                "seller_phone": "9876543210",
                "seller_name": "Ramesh Customer",
                "proposed_seller_payout": 108000,
                "negotiation_status": "offer_sent"
            },
            # 2. Active offer lookup
            {
                "id": 502,
                "counteroffer_number": 2,
                "admin_suggested_price": 108000,
                "status": "pending"
            },
            # 3. Existing conversation lookup
            {"id": 77}
        ]

        executed_sql = []
        def track_execute(query, params=None):
            executed_sql.append((query, params))
        mock_cursor.execute.side_effect = track_execute

        resp = self.client.post(
            "/api/users/bikes/9001/negotiate",
            json={"action": "accept"},
            headers=self.user_a_headers
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["negotiation_status"], "price_accepted")
        self.assertEqual(data["agreed_payout"], 108000.0)

        # Verify buying_price and accepted_seller_payout were written in SQL update
        bike_update_found = False
        for query, params in executed_sql:
            if "UPDATE bikes" in query and "accepted_seller_payout" in query:
                bike_update_found = True
                self.assertIn("buying_price", query)
                self.assertIn("price_accepted", query)
                self.assertIn(108000.0, params)
        self.assertTrue(bike_update_found, "UPDATE bikes did not set buying_price and accepted_seller_payout")

    # -------------------------------------------------------------
    # 8. Admin Final Approval Allowed Once Price Accepted
    # -------------------------------------------------------------
    @patch("app.get_db")
    def test_admin_approve_succeeds_when_price_accepted(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchone.side_effect = [
            # 1. Bike lookup with price_accepted
            {
                "id": 9001,
                "title": "Yamaha MT-15",
                "brand": "Yamaha",
                "model": "MT-15",
                "price": 120000,
                "requested_price": 120000,
                "status": "pending_negotiation",
                "listing_status": "pending_negotiation",
                "negotiation_status": "price_accepted",
                "proposed_seller_payout": 108000,
                "accepted_seller_payout": 108000,
                "buying_price": 108000,
                "seller_id": 101,
                "seller_name": "Ramesh Customer",
                "seller_phone": "9876543210"
            },
            # 2. Existing user lookup
            {"id": 101, "name": "Ramesh Customer", "email": "ramesh@example.com", "phone": "9876543210"},
            # 3. Existing conversation
            {"id": 77},
            # 4. Message idempotency check
            None
        ]

        executed_sql = []
        def track_execute(query, params=None):
            executed_sql.append((query, params))
        mock_cursor.execute.side_effect = track_execute

        resp = self.client.post(
            "/api/admin/bikes/9001/approve",
            json={"approved_price": 135000},
            headers=self.admin_headers
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])

        # Verify buying_price, status='approved', negotiation_status='completed'
        approval_sql_found = False
        for query, params in executed_sql:
            if "UPDATE bikes SET" in query and "status = 'approved'" in query:
                approval_sql_found = True
                self.assertIn("negotiation_status = 'completed'", query)
                self.assertIn(108000.0, params)
        self.assertTrue(approval_sql_found, "Approval SQL did not complete negotiation and lock buying_price")

    # -------------------------------------------------------------
    # 9. Negotiation History Multi-Round Audit Trail
    # -------------------------------------------------------------
    @patch("app.get_db")
    def test_negotiation_rounds_history_endpoint(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchone.return_value = {
            "id": 9001,
            "title": "Yamaha MT-15",
            "seller_id": 101,
            "seller_phone": "9876543210"
        }

        # 2 rounds in history: round 1 was rejected, round 2 was accepted
        mock_cursor.fetchall.return_value = [
            {
                "id": 501,
                "bike_id": 9001,
                "counteroffer_number": 1,
                "admin_name": "admin",
                "admin_suggested_price": 100000,
                "message": "Initial offer",
                "status": "rejected",
                "seller_response_note": "Expected more",
                "created_at": datetime.datetime(2026, 11, 7, 10, 0),
                "responded_at": datetime.datetime(2026, 11, 7, 10, 30)
            },
            {
                "id": 502,
                "bike_id": 9001,
                "counteroffer_number": 2,
                "admin_name": "admin",
                "admin_suggested_price": 108000,
                "message": "Revised offer with tyre upgrade considered",
                "status": "accepted",
                "seller_response_note": None,
                "created_at": datetime.datetime(2026, 11, 7, 11, 0),
                "responded_at": datetime.datetime(2026, 11, 7, 11, 15)
            }
        ]

        # Admin gets full history
        resp = self.client.get("/api/admin/bikes/9001/negotiations", headers=self.admin_headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(len(data["data"]), 2)
        self.assertEqual(data["data"][0]["status"], "rejected")
        self.assertEqual(data["data"][1]["status"], "accepted")

        # Owner gets history
        resp_user = self.client.get("/api/users/bikes/9001/negotiations", headers=self.user_a_headers)
        self.assertEqual(resp_user.status_code, 200)
        self.assertEqual(len(resp_user.get_json()["data"]), 2)

        # Non-owner cannot access history
        resp_other = self.client.get("/api/users/bikes/9001/negotiations", headers=self.user_b_headers)
        self.assertEqual(resp_other.status_code, 403)

if __name__ == "__main__":
    unittest.main()
