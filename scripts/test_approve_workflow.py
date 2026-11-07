import sys
import os
import unittest
import datetime
import jwt
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.getcwd(), "my-node-app"))

from app import app, JWT_SECRET

class TestBikeApprovalWorkflow(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        app.config["TESTING"] = True
        
        # Generate valid admin JWT token
        payload = {
            "id": 1,
            "username": "admin",
            "role": "superadmin",
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)
        }
        self.admin_token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
        self.headers = {
            "Authorization": f"Bearer {self.admin_token}",
            "Content-Type": "application/json"
        }

    def test_price_validation_negative(self):
        resp = self.client.post(
            "/api/admin/bikes/660001/approve",
            json={"approved_price": -500},
            headers=self.headers
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertFalse(data["success"])
        self.assertIn("between ₹0 and ₹10,00,000", data["message"])

    def test_price_validation_exceeds_max(self):
        resp = self.client.post(
            "/api/admin/bikes/660001/approve",
            json={"approved_price": 1000001},
            headers=self.headers
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertFalse(data["success"])
        self.assertIn("between ₹0 and ₹10,00,000", data["message"])

    def test_price_validation_invalid_type(self):
        resp = self.client.post(
            "/api/admin/bikes/660001/approve",
            json={"approved_price": "invalid_abc"},
            headers=self.headers
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertFalse(data["success"])
        self.assertIn("valid number", data["message"])

    @patch("app.get_db")
    def test_approval_workflow_success_for_bike_660001(self, mock_get_db):
        """
        Tests approving bike 660001. Verifies that bikes table uses seller_id (not user_id),
        and chat_conversations uses updated_at (never last_message_at).
        """
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Bike record exists
        mock_cursor.fetchone.side_effect = [
            # 1. Bike query
            {
                "id": 660001,
                "title": "Royal Enfield Hunter 350 Dapper Ash",
                "brand": "Royal Enfield",
                "model": "Hunter 350",
                "price": 149000,
                "requested_price": 149000,
                "status": "pending",
                "listing_status": "pending",
                "seller_id": 42,
                "seller_name": "Ramesh",
                "seller_phone": "9876543210"
            },
            # 2. Existing chat_conversations query (returns None so it inserts new)
            None,
            # 3. Already sent query (returns None)
            None
        ]

        mock_cursor.lastrowid = 888

        executed_queries = []
        def track_execute(query, params=None):
            executed_queries.append((query, params))

        mock_cursor.execute.side_effect = track_execute

        resp = self.client.post(
            "/api/admin/bikes/660001/approve",
            json={"approved_price": 145000},
            headers=self.headers
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertIn("accepted and published", data["message"])
        self.assertEqual(data["data"]["bike_id"], 660001)
        self.assertEqual(data["data"]["price"], 145000.0)

        # Check commit was called
        mock_conn.commit.assert_called()

        # Check that NO query references last_message_at
        for q, _ in executed_queries:
            self.assertNotIn("last_message_at", q, f"Query incorrectly references last_message_at: {q}")
            if "FROM bikes" in q:
                self.assertNotIn("user_id", q, f"Query on bikes incorrectly references user_id: {q}")

    @patch("app.get_db")
    def test_approval_idempotency_prevents_duplicate_messages(self, mock_get_db):
        """
        If the admin clicks 'Confirm & Publish' repeatedly on bike 660001,
        the acceptance document request message must NOT be duplicated.
        """
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchone.side_effect = [
            # 1. Bike query
            {
                "id": 660001,
                "title": "Royal Enfield Hunter 350 Dapper Ash",
                "brand": "Royal Enfield",
                "model": "Hunter 350",
                "price": 145000,
                "status": "approved",
                "listing_status": "accepted",
                "seller_id": 42,
                "seller_name": "Ramesh",
                "seller_phone": "9876543210"
            },
            # 2. Existing chat_conversations query (found conversation 500)
            {"id": 500},
            # 3. Already sent query: returns existing message record!
            {"id": 1234}
        ]

        executed_queries = []
        def track_execute(query, params=None):
            executed_queries.append(query)

        mock_cursor.execute.side_effect = track_execute

        resp = self.client.post(
            "/api/admin/bikes/660001/approve",
            json={"approved_price": 145000},
            headers=self.headers
        )
        self.assertEqual(resp.status_code, 200)

        # Confirm INSERT INTO chat_messages was NOT called because message already sent
        insert_msg_queries = [q for q in executed_queries if "INSERT INTO chat_messages" in q]
        self.assertEqual(len(insert_msg_queries), 0, "Duplicate chat message was mistakenly inserted!")

    @patch("app.get_db")
    def test_chat_failure_does_not_break_bike_approval(self, mock_get_db):
        """
        If chat insertion fails (e.g., temporary lock or message failure),
        the bike approval must STILL succeed and commit without HTTP 500.
        """
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchone.side_effect = [
            # 1. Bike query
            {
                "id": 660001,
                "title": "Royal Enfield Hunter 350 Dapper Ash",
                "brand": "Royal Enfield",
                "model": "Hunter 350",
                "price": 145000,
                "status": "pending",
                "listing_status": "pending",
                "seller_id": 42,
                "seller_name": "Ramesh",
                "seller_phone": "9876543210"
            },
            # 2. User lookup
            {"id": 42, "name": "Ramesh", "email": "ramesh@example.com", "phone": "9876543210"},
            # 3. Query conversation throws exception
            Exception("Simulated chat database lock")
        ]

        resp = self.client.post(
            "/api/admin/bikes/660001/approve",
            json={"approved_price": 145000},
            headers=self.headers
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["status"], "approved")
        self.assertFalse(data["data"]["chat_delivered"])

if __name__ == "__main__":
    unittest.main()
