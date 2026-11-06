import sys
import os
import unittest
import datetime
import jwt
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.getcwd(), "my-node-app"))

from app import app, JWT_SECRET

class TestContactMessagesWorkflow(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        app.config["TESTING"] = True

        # Valid Admin Token
        admin_payload = {
            "id": 1,
            "username": "admin",
            "role": "admin",
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)
        }
        self.admin_token = jwt.encode(admin_payload, JWT_SECRET, algorithm="HS256")
        self.admin_headers = {"Authorization": f"Bearer {self.admin_token}"}

        # Normal User Token (should be rejected for admin endpoints)
        user_payload = {
            "id": 99,
            "username": "customer_user",
            "role": "user",
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)
        }
        self.user_token = jwt.encode(user_payload, JWT_SECRET, algorithm="HS256")
        self.user_headers = {"Authorization": f"Bearer {self.user_token}"}

        self.valid_contact_data = {
            "name": "Kavitha Rajan",
            "email": "kavitha.rajan.test@example.com",
            "phone": "+91 98765 43210",
            "subject": "Yamaha MT-15 Inspection & Booking Inquiry",
            "message": "Hello SMR Motors, I am interested in inspecting the 2022 Yamaha MT-15 listed on your showroom. Could we schedule a viewing and test ride this Saturday at 11 AM?"
        }

    # ==========================================
    # 1. SERVER-SIDE VALIDATION TESTS
    # ==========================================
    def test_missing_name_rejected(self):
        payload = dict(self.valid_contact_data)
        payload["name"] = "A" # Too short
        resp = self.client.post("/api/contact", json=payload)
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertFalse(data["success"])
        self.assertIn("Full name must be at least 2 characters", data["message"])

    def test_invalid_email_rejected(self):
        payload = dict(self.valid_contact_data)
        payload["email"] = "not-an-email"
        resp = self.client.post("/api/contact", json=payload)
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertFalse(data["success"])
        self.assertIn("valid email address", data["message"])

    def test_short_mobile_rejected(self):
        payload = dict(self.valid_contact_data)
        payload["phone"] = "98765" # Less than 10 digits
        resp = self.client.post("/api/contact", json=payload)
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertFalse(data["success"])
        self.assertIn("at least 10 valid digits", data["message"])

    def test_missing_subject_rejected(self):
        payload = dict(self.valid_contact_data)
        payload["subject"] = ""
        resp = self.client.post("/api/contact", json=payload)
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertFalse(data["success"])
        self.assertIn("subject must be at least 3 characters", data["message"])

    def test_short_message_rejected(self):
        payload = dict(self.valid_contact_data)
        payload["message"] = "Hi" # Less than 5 characters
        resp = self.client.post("/api/contact", json=payload)
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertFalse(data["success"])
        self.assertIn("at least 5 characters", data["message"])

    # ==========================================
    # 2. GUEST SUBMISSION (NO LOGIN REQUIRED)
    # ==========================================
    @patch("app.get_db")
    def test_guest_submission_creates_message_with_status_new(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 8801
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        executed_queries = []
        def track_execute(query, params=None):
            executed_queries.append((query, params))
        mock_cursor.execute.side_effect = track_execute

        resp = self.client.post("/api/contact", json=self.valid_contact_data)
        self.assertEqual(resp.status_code, 201)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["id"], 8801)
        self.assertEqual(data["data"]["status"], "new")
        self.assertEqual(data["data"]["name"], "Kavitha Rajan")
        self.assertEqual(data["data"]["email"], "kavitha.rajan.test@example.com")
        self.assertEqual(data["data"]["phone"], "+91 98765 43210")
        self.assertEqual(data["data"]["subject"], "Yamaha MT-15 Inspection & Booking Inquiry")

        # Verify SQL INSERT into contact_messages
        insert_queries = [q for q, p in executed_queries if "INSERT INTO contact_messages" in q]
        self.assertTrue(len(insert_queries) > 0, "INSERT INTO contact_messages was not executed!")
        mock_conn.commit.assert_called()

    # ==========================================
    # 3. ADMIN LIST INBOUND INQUIRIES
    # ==========================================
    @patch("app.get_db")
    def test_admin_get_contact_messages_list_and_counts(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock status counts query results
        count_row = {
            "total": 14,
            "cnt_new": 3,
            "cnt_read": 5,
            "cnt_replied": 2,
            "cnt_resolved": 4
        }

        # Mock message records
        message_rows = [
            {
                "id": 8801,
                "name": "Kavitha Rajan",
                "email": "kavitha.rajan.test@example.com",
                "phone": "+91 98765 43210",
                "subject": "Yamaha MT-15 Inspection & Booking Inquiry",
                "message": "Hello SMR Motors, I am interested in inspecting the 2022 Yamaha MT-15 listed on your showroom.",
                "status": "new",
                "created_at": "2026-11-06 14:30:00"
            },
            {
                "id": 8800,
                "name": "Suresh Kumar",
                "email": "suresh@example.com",
                "phone": "9840123456",
                "subject": "Royal Enfield Classic 350 Trade-In",
                "message": "Looking to trade in my 2019 Classic 350 for a newer model.",
                "status": "read",
                "created_at": "2026-11-05 10:15:00"
            }
        ]

        # Mock cursor.fetchone for counts, and cursor.fetchall for messages list
        mock_cursor.fetchone.return_value = count_row
        mock_cursor.fetchall.return_value = message_rows

        resp = self.client.get("/api/admin/contact-messages", headers=self.admin_headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertIn("counts", data)
        self.assertIn("data", data)

        counts = data["counts"]
        self.assertEqual(counts["new"], 3)
        self.assertEqual(counts["read"], 5)
        self.assertEqual(counts["replied"], 2)
        self.assertEqual(counts["resolved"], 4)
        self.assertEqual(counts["total"], 14)

        messages = data["data"]
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["name"], "Kavitha Rajan")
        self.assertEqual(messages[0]["phone"], "+91 98765 43210")
        self.assertEqual(messages[0]["subject"], "Yamaha MT-15 Inspection & Booking Inquiry")

    # ==========================================
    # 4. ADMIN GET MESSAGE DETAILS & AUTO-MARK READ
    # ==========================================
    @patch("app.get_db")
    def test_admin_get_message_details_auto_marks_read(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        message_record = {
            "id": 8801,
            "name": "Kavitha Rajan",
            "email": "kavitha.rajan.test@example.com",
            "phone": "+91 98765 43210",
            "subject": "Yamaha MT-15 Inspection & Booking Inquiry",
            "message": "Hello SMR Motors, I am interested in inspecting the 2022 Yamaha MT-15 listed on your showroom.",
            "status": "new",
            "admin_reply": None,
            "replied_at": None,
            "resolved_at": None,
            "created_at": "2026-11-06 14:30:00"
        }

        mock_cursor.fetchone.side_effect = [
            message_record
        ]
        mock_cursor.fetchall.side_effect = [
            [] # No previous replies in thread
        ]

        executed_queries = []
        def track_execute(query, params=None):
            executed_queries.append((query, params))
        mock_cursor.execute.side_effect = track_execute

        resp = self.client.get("/api/admin/contact-messages/8801", headers=self.admin_headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["status"], "read") # auto-advanced from new to read

        # Verify UPDATE contact_messages SET status = 'read' was executed
        update_read = [q for q, p in executed_queries if "UPDATE contact_messages" in q and "status = 'read'" in q]
        self.assertTrue(len(update_read) > 0, "Auto-mark as read UPDATE query was not executed!")
        mock_conn.commit.assert_called()

    # ==========================================
    # 5. ADMIN UPDATE STATUS (RESOLVED)
    # ==========================================
    @patch("app.get_db")
    def test_admin_update_status_resolved(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchone.side_effect = [
            {"id": 8801, "status": "read"}
        ]

        executed_queries = []
        def track_execute(query, params=None):
            executed_queries.append((query, params))
        mock_cursor.execute.side_effect = track_execute

        resp = self.client.patch("/api/admin/contact-messages/8801/status", json={"status": "resolved"}, headers=self.admin_headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["status"], "resolved")

        update_status = [q for q, p in executed_queries if "UPDATE contact_messages" in q and ("status = 'resolved'" in q or "status = %s" in q)]
        self.assertTrue(len(update_status) > 0, "Status update query was not executed!")
        mock_conn.commit.assert_called()

    # ==========================================
    # 6. ADMIN REPLY TO MESSAGE
    # ==========================================
    @patch("app.get_db")
    def test_admin_reply_to_message_records_and_updates_status(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        message_record = {
            "id": 8801,
            "name": "Kavitha Rajan",
            "email": "kavitha.rajan.test@example.com",
            "phone": "+91 98765 43210",
            "subject": "Yamaha MT-15 Inspection & Booking Inquiry",
            "status": "read"
        }

        mock_cursor.fetchone.side_effect = [
            message_record
        ]

        executed_queries = []
        def track_execute(query, params=None):
            executed_queries.append((query, params))
        mock_cursor.execute.side_effect = track_execute

        reply_payload = {
            "reply": "Dear Kavitha, thank you for reaching out! We have reserved a test ride slot for you this Saturday at 11:00 AM."
        }

        resp = self.client.post("/api/admin/contact-messages/8801/reply", json=reply_payload, headers=self.admin_headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["status"], "replied")
        self.assertIn("delivery_note", data["data"])

        # Verify reply stored in contact_replies and contact_messages updated
        insert_reply = [q for q, p in executed_queries if "INSERT INTO contact_replies" in q]
        self.assertTrue(len(insert_reply) > 0, "INSERT INTO contact_replies was not executed!")
        update_replied = [q for q, p in executed_queries if "UPDATE contact_messages" in q and "status = 'replied'" in q]
        self.assertTrue(len(update_replied) > 0, "UPDATE contact_messages SET status = 'replied' was not executed!")
        mock_conn.commit.assert_called()

    # ==========================================
    # 7. ADMIN DELETE MESSAGE
    # ==========================================
    @patch("app.get_db")
    def test_admin_delete_message(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchone.side_effect = [
            {"id": 8801, "name": "Kavitha Rajan"}
        ]

        executed_queries = []
        def track_execute(query, params=None):
            executed_queries.append((query, params))
        mock_cursor.execute.side_effect = track_execute

        resp = self.client.delete("/api/admin/contact-messages/8801", headers=self.admin_headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertIn("deleted successfully", data["message"].lower())

        delete_query = [q for q, p in executed_queries if "DELETE FROM contact_messages" in q]
        self.assertTrue(len(delete_query) > 0, "DELETE FROM contact_messages was not executed!")
        mock_conn.commit.assert_called()

    # ==========================================
    # 8. AUTHORIZATION GUARDS
    # ==========================================
    def test_unauthorized_access_rejected(self):
        # Missing auth header
        resp = self.client.get("/api/admin/contact-messages")
        self.assertEqual(resp.status_code, 401)

        # Normal user role token
        resp = self.client.get("/api/admin/contact-messages", headers=self.user_headers)
        self.assertEqual(resp.status_code, 403)

if __name__ == "__main__":
    unittest.main()
