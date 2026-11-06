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
            "/api/admin/bikes/99/approve",
            json={"approved_price": -500},
            headers=self.headers
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertFalse(data["success"])
        self.assertIn("between ₹0 and ₹10,00,000", data["message"])

    def test_price_validation_exceeds_max(self):
        resp = self.client.post(
            "/api/admin/bikes/99/approve",
            json={"approved_price": 1000001},
            headers=self.headers
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertFalse(data["success"])
        self.assertIn("between ₹0 and ₹10,00,000", data["message"])

    def test_price_validation_invalid_type(self):
        resp = self.client.post(
            "/api/admin/bikes/99/approve",
            json={"approved_price": "abc_invalid"},
            headers=self.headers
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertFalse(data["success"])
        self.assertIn("valid number", data["message"])

    @patch("app.get_db")
    def test_approval_workflow_success_with_fallback_when_last_message_at_missing(self, mock_get_db):
        """
        Simulates TiDB throwing Error 1054 Unknown column 'last_message_at' on UPDATE chat_conversations.
        The backend must catch this and fall back to UPDATE chat_conversations SET updated_at = CURRENT_TIMESTAMP
        without failing the request!
        """
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Bike record exists
        mock_cursor.fetchone.side_effect = [
            # 1. Bike query
            {
                "id": 101,
                "title": "Royal Enfield Hunter 350",
                "brand": "Royal Enfield",
                "model": "Hunter 350",
                "price": 149000,
                "status": "pending",
                "listing_status": "pending",
                "seller_id": 42,
                "seller_name": "Ramesh",
                "seller_phone": "9876543210",
                "user_id": 42
            },
            # 2. Existing chat_conversations query (returns None so it inserts new)
            None,
            # 3. Already sent query (returns None)
            None
        ]

        mock_cursor.lastrowid = 888

        executed_queries = []
        def track_execute(query, params=None):
            executed_queries.append(query)
            # Simulate TiDB error 1054 when query has last_message_at
            if "last_message_at" in query and "UPDATE chat_conversations" in query:
                raise Exception("1054 (42S22): Unknown column 'last_message_at' in 'field list'")

        mock_cursor.execute.side_effect = track_execute

        resp = self.client.post(
            "/api/admin/bikes/101/approve",
            json={"approved_price": 145000},
            headers=self.headers
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertIn("accepted and published", data["message"])

        # Check commit was called
        mock_conn.commit.assert_called()

        # Check that fallback query without last_message_at was executed!
        fallback_queries = [q for q in executed_queries if "UPDATE chat_conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = %s" in q]
        self.assertTrue(len(fallback_queries) > 0, "Fallback query without last_message_at was not executed!")

    @patch("app.get_db")
    def test_approval_idempotency_prevents_duplicate_messages(self, mock_get_db):
        """
        If the admin clicks 'Confirm & Publish' again, the acceptance document request message must NOT be duplicated.
        """
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchone.side_effect = [
            # 1. Bike query
            {
                "id": 102,
                "title": "Yamaha MT-15",
                "brand": "Yamaha",
                "model": "MT-15",
                "price": 120000,
                "status": "approved",
                "listing_status": "accepted",
                "seller_id": 55,
                "seller_name": "Suresh",
                "seller_phone": "9998887776",
                "user_id": 55
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
            "/api/admin/bikes/102/approve",
            json={"approved_price": 120000},
            headers=self.headers
        )
        self.assertEqual(resp.status_code, 200)

        # Confirm INSERT INTO chat_messages was NOT called because message already sent
        insert_msg_queries = [q for q in executed_queries if "INSERT INTO chat_messages" in q]
        self.assertEqual(len(insert_msg_queries), 0, "Duplicate chat message was mistakenly inserted!")

    @patch("app.get_db")
    def test_doc_verify_workflow_with_fallback_when_last_message_at_missing(self, mock_get_db):
        """
        Simulates document verification when last_message_at column is missing.
        """
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchone.side_effect = [
            # 1. Document record query
            {
                "id": 10,
                "bike_id": 101,
                "user_id": 42,
                "document_type": "rc_book",
                "status": "pending",
                "customer_name": "Ramesh",
                "bike_brand": "Royal Enfield",
                "bike_model": "Hunter 350"
            },
            # 2. Existing chat_conversations query
            {"id": 888}
        ]

        executed_queries = []
        def track_execute(query, params=None):
            executed_queries.append(query)
            if "last_message_at" in query and "UPDATE chat_conversations" in query:
                raise Exception("1054 (42S22): Unknown column 'last_message_at' in 'field list'")

        mock_cursor.execute.side_effect = track_execute

        resp = self.client.post(
            "/api/admin/bikes/101/documents/10/verify",
            json={"status": "approved", "remarks": "RC book verified and clear"},
            headers=self.headers
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertIn("approved", data["message"].lower())

        fallback_queries = [q for q in executed_queries if "UPDATE chat_conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = %s" in q]
        self.assertTrue(len(fallback_queries) > 0, "Fallback query without last_message_at was not executed in doc verify!")

if __name__ == "__main__":
    unittest.main()
