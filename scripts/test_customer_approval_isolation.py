import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
import unittest
import datetime
import jwt
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "my-node-app"))
from app import app, JWT_SECRET

class TestCustomerApprovalIsolation(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        app.config["TESTING"] = True

        # Generate tokens for Admin and 3 Customers
        now = datetime.datetime.now(datetime.timezone.utc)
        exp = now + datetime.timedelta(hours=2)

        self.admin_token = jwt.encode({"id": 1, "username": "admin", "role": "superadmin", "exp": exp}, JWT_SECRET, algorithm="HS256")
        self.cust_a_token = jwt.encode({"id": 101, "email": "alpha@example.com", "name": "Customer Alpha", "role": "user", "exp": exp}, JWT_SECRET, algorithm="HS256")
        self.cust_b_token = jwt.encode({"id": 102, "email": "beta@example.com", "name": "Customer Beta", "role": "user", "exp": exp}, JWT_SECRET, algorithm="HS256")
        self.cust_c_token = jwt.encode({"id": 103, "email": "gamma@example.com", "name": "Customer Gamma", "role": "user", "exp": exp}, JWT_SECRET, algorithm="HS256")

        self.admin_headers = {"Authorization": f"Bearer {self.admin_token}", "Content-Type": "application/json"}
        self.cust_a_headers = {"Authorization": f"Bearer {self.cust_a_token}", "Content-Type": "application/json"}
        self.cust_b_headers = {"Authorization": f"Bearer {self.cust_b_token}", "Content-Type": "application/json"}
        self.cust_c_headers = {"Authorization": f"Bearer {self.cust_c_token}", "Content-Type": "application/json"}

    @patch("app.get_db")
    def test_guest_submission_blocked(self, mock_get_db):
        """Unauthenticated / guest submissions must be rejected with 401."""
        resp = self.client.post("/api/bikes", json={
            "title": "2023 Royal Enfield Classic 350",
            "brand": "Royal Enfield",
            "model": "Classic 350",
            "year": 2023,
            "price": 180000
        })
        self.assertEqual(resp.status_code, 401)
        data = resp.get_json()
        self.assertFalse(data["success"])
        self.assertIn("Authentication required", data["message"])

    @patch("app.get_db")
    def test_customer_submission_security_and_association(self, mock_get_db):
        """
        Customer A submits a bike.
        Even if body passes spoofed seller_id: 999, backend must bind strictly to Customer A (101).
        """
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock user lookup returning Customer Alpha
        mock_cursor.fetchone.side_effect = [
            {"id": 101, "name": "Customer Alpha", "email": "alpha@example.com", "phone": "9876543210"},
            {"id": 660001, "status": "pending", "listing_status": "pending"} # verification select
        ]
        mock_cursor.lastrowid = 660001

        executed_queries = []
        def track_execute(query, params=None):
            executed_queries.append((query, params))

        mock_cursor.execute.side_effect = track_execute

        resp = self.client.post(
            "/api/bikes",
            json={
                "title": "2022 Hunter 350 Dapper Ash",
                "brand": "Royal Enfield",
                "model": "Hunter 350",
                "year": 2022,
                "price": 149000,
                "seller_id": 999,  # Spoofed! Must be ignored!
                "seller_name": "Spoofed Attacker"
            },
            headers=self.cust_a_headers
        )

        self.assertEqual(resp.status_code, 201)
        data = resp.get_json()
        self.assertTrue(data["success"])

        # Check insert into bikes table
        insert_bikes_calls = [c for c in executed_queries if "INSERT INTO bikes " in c[0]]
        self.assertTrue(len(insert_bikes_calls) > 0)
        params = insert_bikes_calls[0][1]

        # Verify seller_id is 101 (Customer Alpha) NOT 999
        # In INSERT INTO bikes, params tuple has seller_id at index 14
        self.assertIn(101, params)
        self.assertNotIn(999, params)
        self.assertIn("Customer Alpha", params)
        self.assertNotIn("Spoofed Attacker", params)

    @patch("app.get_db")
    def test_admin_approval_strict_customer_isolation(self, mock_get_db):
        """
        When Admin approves Bike A (belonging to Customer A / ID 101):
        - Conversation created for user_id = 101, bike_id = 660001.
        - Approval message sent only to Customer Alpha.
        - Message matches the exact 4-point document requirement.
        - In-app notification sent only to Customer Alpha.
        - Customer Beta (102) and Gamma (103) receive nothing.
        """
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # 1. Bike query returns Bike A owned by Customer Alpha (seller_id 101)
        mock_cursor.fetchone.side_effect = [
            {
                "id": 660001,
                "title": "Royal Enfield Hunter 350",
                "brand": "Royal Enfield",
                "model": "Hunter 350",
                "price": 149000,
                "requested_price": 149000,
                "status": "pending",
                "listing_status": "pending",
                "seller_id": 101,
                "seller_name": "Customer Alpha",
                "seller_phone": "9876543210"
            },
            # 2. User lookup for seller_id 101
            {"id": 101, "name": "Customer Alpha", "email": "alpha@example.com", "phone": "9876543210"},
            # 3. Chat conversation lookup (returns None, creates new)
            None,
            # 4. Message already sent check (returns None)
            None,
            # 5. Notification check (returns None)
            None
        ]
        mock_cursor.lastrowid = 501 # conv_id

        executed_queries = []
        def track_execute(query, params=None):
            executed_queries.append((query, params))

        mock_cursor.execute.side_effect = track_execute

        resp = self.client.post(
            "/api/admin/bikes/660001/approve",
            json={"approved_price": 145000},
            headers=self.admin_headers
        )

        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertTrue(data["data"]["chat_delivered"])

        # 1. Verify chat_conversations search strictly isolates user_id=101 AND bike_id=660001
        conv_selects = [c for c in executed_queries if "SELECT id FROM chat_conversations" in c[0]]
        self.assertTrue(len(conv_selects) > 0)
        query_str, query_params = conv_selects[0]
        self.assertIn("user_id = %s AND bike_id = %s", query_str)
        self.assertEqual(query_params, (101, 660001))

        # 2. Verify chat_messages insert
        msg_inserts = [c for c in executed_queries if "INSERT INTO chat_messages" in c[0]]
        self.assertTrue(len(msg_inserts) > 0)
        _, msg_params = msg_inserts[0]
        msg_body = msg_params[2]

        self.assertIn("Hello Customer Alpha,", msg_body)
        self.assertIn("Good news! Your bike Royal Enfield Hunter 350 has been accepted by SMR Motors.", msg_body)
        self.assertIn("Required documents:\n1. RC Book\n2. Valid Insurance\n3. Owner Identity Proof\n4. Other relevant vehicle documents, if required.", msg_body)
        self.assertIn("Please log in to your SMR Motors account and upload the documents for verification.", msg_body)
        self.assertIn("Thank you,\nSMR Motors Team", msg_body)

        # 3. Verify notification strictly targets user_id = 101
        notif_inserts = [c for c in executed_queries if "INSERT INTO notifications" in c[0]]
        self.assertTrue(len(notif_inserts) > 0)
        _, notif_params = notif_inserts[0]
        self.assertEqual(notif_params[0], 101)  # user_id
        self.assertIn("Bike Submission Accepted! Documents Required", notif_params[2])

        # 4. Verify no queries contain user 102 or 103
        for q, p in executed_queries:
            if p:
                self.assertNotIn(102, p)
                self.assertNotIn(103, p)

    @patch("app.get_db")
    def test_approval_idempotency(self, mock_get_db):
        """
        Approving a bike a second time must NOT send duplicate acceptance messages.
        """
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock existing bike and existing message
        mock_cursor.fetchone.side_effect = [
            {
                "id": 660001,
                "title": "Royal Enfield Hunter 350",
                "brand": "Royal Enfield",
                "model": "Hunter 350",
                "price": 145000,
                "requested_price": 149000,
                "status": "approved",
                "listing_status": "accepted",
                "seller_id": 101,
                "seller_name": "Customer Alpha",
                "seller_phone": "9876543210"
            },
            {"id": 101, "name": "Customer Alpha", "email": "alpha@example.com", "phone": "9876543210"},
            # Existing conversation found
            {"id": 501},
            # Already sent check returns existing message ID!
            {"id": 9901},
            # Notification check returns existing notification ID!
            {"id": 8801}
        ]

        executed_queries = []
        def track_execute(query, params=None):
            executed_queries.append((query, params))

        mock_cursor.execute.side_effect = track_execute

        resp = self.client.post(
            "/api/admin/bikes/660001/approve",
            json={"approved_price": 145000},
            headers=self.admin_headers
        )

        self.assertEqual(resp.status_code, 200)
        # Verify NO new chat_messages was inserted!
        msg_inserts = [c for c in executed_queries if "INSERT INTO chat_messages" in c[0]]
        self.assertEqual(len(msg_inserts), 0)

        # Verify NO new notification was inserted!
        notif_inserts = [c for c in executed_queries if "INSERT INTO notifications" in c[0]]
        self.assertEqual(len(notif_inserts), 0)

    @patch("app.get_db")
    def test_multi_customer_approval_messages_never_cross_deliver(self, mock_get_db):
        """
        Verify that approving Customer B's bike delivers to Customer B (102),
        and approving Customer C's bike delivers to Customer C (103),
        with ZERO message leakage to Customer A (101) or between customers.
        """
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Simulation 1: Admin approves Bike 770002 belonging to Customer Beta (102)
        mock_cursor.fetchone.side_effect = [
            # Bike 770002
            {
                "id": 770002,
                "title": "Yamaha MT-15 V2",
                "brand": "Yamaha",
                "model": "MT-15 V2",
                "price": 140000,
                "requested_price": 140000,
                "status": "pending",
                "listing_status": "pending",
                "seller_id": 102,
                "seller_name": "Customer Beta",
                "seller_phone": "9811122233"
            },
            # User 102 lookup
            {"id": 102, "name": "Customer Beta", "email": "beta@example.com", "phone": "9811122233"},
            # Chat conv check
            None,
            # Message check
            None,
            # Notification check
            None
        ]
        mock_cursor.lastrowid = 602 # conv_id for Beta

        executed_queries = []
        def track_execute(query, params=None):
            executed_queries.append((query, params))

        mock_cursor.execute.side_effect = track_execute

        resp_b = self.client.post(
            "/api/admin/bikes/770002/approve",
            json={"approved_price": 138000},
            headers=self.admin_headers
        )

        self.assertEqual(resp_b.status_code, 200)

        # Verify chat conversation created for user_id = 102, bike_id = 770002
        conv_inserts_b = [c for c in executed_queries if "INSERT INTO chat_conversations" in c[0]]
        self.assertEqual(len(conv_inserts_b), 1)
        self.assertEqual(conv_inserts_b[0][1][0], 102) # user_id 102
        self.assertEqual(conv_inserts_b[0][1][1], 770002) # bike_id 770002

        # Verify message content contains Customer Beta and Yamaha MT-15 V2
        msg_inserts_b = [c for c in executed_queries if "INSERT INTO chat_messages" in c[0]]
        self.assertEqual(len(msg_inserts_b), 1)
        self.assertIn("Hello Customer Beta,", msg_inserts_b[0][1][2])
        self.assertIn("Your bike Yamaha MT-15 V2 has been accepted by SMR Motors.", msg_inserts_b[0][1][2])

        # Verify Customer A (101) was NEVER referenced
        for q, p in executed_queries:
            if p:
                self.assertNotIn(101, p)
                self.assertNotIn("Customer Alpha", p)

        # Simulation 2: Admin approves Bike 770003 belonging to Customer Gamma (103)
        executed_queries.clear()
        mock_cursor.fetchone.side_effect = [
            # Bike 770003
            {
                "id": 770003,
                "title": "KTM Duke 250",
                "brand": "KTM",
                "model": "Duke 250",
                "price": 180000,
                "requested_price": 180000,
                "status": "pending",
                "listing_status": "pending",
                "seller_id": 103,
                "seller_name": "Customer Gamma",
                "seller_phone": "9899988877"
            },
            # User 103 lookup
            {"id": 103, "name": "Customer Gamma", "email": "gamma@example.com", "phone": "9899988877"},
            # Chat conv check
            None,
            # Message check
            None,
            # Notification check
            None
        ]
        mock_cursor.lastrowid = 603 # conv_id for Gamma

        resp_c = self.client.post(
            "/api/admin/bikes/770003/approve",
            json={"approved_price": 175000},
            headers=self.admin_headers
        )

        self.assertEqual(resp_c.status_code, 200)

        # Verify chat conversation created for user_id = 103, bike_id = 770003
        conv_inserts_c = [c for c in executed_queries if "INSERT INTO chat_conversations" in c[0]]
        self.assertEqual(len(conv_inserts_c), 1)
        self.assertEqual(conv_inserts_c[0][1][0], 103) # user_id 103
        self.assertEqual(conv_inserts_c[0][1][1], 770003) # bike_id 770003

        # Verify message content contains Customer Gamma and KTM Duke 250
        msg_inserts_c = [c for c in executed_queries if "INSERT INTO chat_messages" in c[0]]
        self.assertEqual(len(msg_inserts_c), 1)
        self.assertIn("Hello Customer Gamma,", msg_inserts_c[0][1][2])
        self.assertIn("Your bike KTM Duke 250 has been accepted by SMR Motors.", msg_inserts_c[0][1][2])

        # Verify Customer Alpha (101) and Customer Beta (102) were NEVER referenced
        for q, p in executed_queries:
            if p:
                self.assertNotIn(101, p)
                self.assertNotIn(102, p)
                self.assertNotIn("Customer Alpha", p)
                self.assertNotIn("Customer Beta", p)

if __name__ == "__main__":
    unittest.main()
