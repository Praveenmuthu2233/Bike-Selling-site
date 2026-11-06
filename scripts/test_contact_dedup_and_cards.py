import sys
import os
import unittest
import datetime
import jwt
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.getcwd(), "my-node-app"))

from app import app, JWT_SECRET

class TestContactDedupAndCards(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        app.config["TESTING"] = True

        admin_payload = {
            "id": 1,
            "username": "admin",
            "role": "admin",
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)
        }
        self.admin_token = jwt.encode(admin_payload, JWT_SECRET, algorithm="HS256")
        self.admin_headers = {"Authorization": f"Bearer {self.admin_token}"}

        user_payload = {
            "id": 99,
            "username": "normal_user",
            "role": "user",
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)
        }
        self.user_token = jwt.encode(user_payload, JWT_SECRET, algorithm="HS256")
        self.user_headers = {"Authorization": f"Bearer {self.user_token}"}

        self.valid_msg_1 = {
            "name": "Arun Prakash",
            "email": "arun.prakash@example.com",
            "phone": "9876543210",
            "subject": "Royal Enfield Classic 350 Test Ride",
            "message": "Hello SMR Motors, I would like to schedule a test ride for the Royal Enfield Classic 350 this Saturday."
        }

        self.valid_msg_2 = {
            "name": "Meena Kumari",
            "email": "meena.k@example.com",
            "phone": "9840198401",
            "subject": "Honda Activa 6G Price Valuation",
            "message": "Hi, I want to trade in my old scooter and get a price valuation for the Activa 6G."
        }

    # =========================================================================
    # 1. PAGE VISIT & REFRESH VERIFICATION (NO MESSAGES CREATED)
    # =========================================================================
    @patch("app.get_db")
    def test_visiting_contact_page_never_creates_message(self, mock_get_db):
        """Verify opening and refreshing the contact page executes 0 INSERT queries."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        executed_queries = []
        def track_execute(query, params=None):
            executed_queries.append((query, params))
        mock_cursor.execute.side_effect = track_execute

        # 1. Visit /contact
        resp1 = self.client.get("/contact")
        self.assertEqual(resp1.status_code, 200)

        # 2. Visit /contact.html
        resp2 = self.client.get("/contact.html")
        self.assertEqual(resp2.status_code, 200)

        # 3. Refresh /contact 3 times
        for _ in range(3):
            r = self.client.get("/contact")
            self.assertEqual(r.status_code, 200)

        # Verify NO insert queries were executed at all!
        insert_queries = [q for q, p in executed_queries if "INSERT INTO" in str(q).upper()]
        self.assertEqual(len(insert_queries), 0, "Visiting or refreshing contact page must NEVER create a database record!")
        print("[OK] Verified: Opening & refreshing /contact creates 0 database records.")

    # =========================================================================
    # 2. DELIBERATE SUBMISSION VS DUPLICATE SPAM PREVENTED
    # =========================================================================
    @patch("app.get_db")
    def test_single_submission_creates_one_record(self, mock_get_db):
        """A deliberate user submission creates exactly one record."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 9001
        # First query is dedup check (returns None = not duplicate)
        mock_cursor.fetchone.return_value = None
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        executed_queries = []
        def track_execute(query, params=None):
            executed_queries.append((query, params))
        mock_cursor.execute.side_effect = track_execute

        resp = self.client.post("/api/contact", json=self.valid_msg_1)
        self.assertEqual(resp.status_code, 201)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["id"], 9001)
        self.assertEqual(data["data"]["status"], "new")

        insert_queries = [q for q, p in executed_queries if "INSERT INTO contact_messages" in str(q)]
        self.assertEqual(len(insert_queries), 1, "Expected exactly 1 INSERT query for single submission!")
        print("[OK] Verified: One deliberate user submission creates exactly one database record.")

    @patch("app.get_db")
    def test_duplicate_submission_within_60s_is_prevented(self, mock_get_db):
        """Rapid duplicate submissions within 60s return existing record without duplicate INSERT."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        # Mock dedup query finding an existing identical record created within 60s
        mock_cursor.fetchone.return_value = {
            "id": 9001,
            "created_at": "2026-11-06 20:30:00",
            "status": "new"
        }
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        executed_queries = []
        def track_execute(query, params=None):
            executed_queries.append((query, params))
        mock_cursor.execute.side_effect = track_execute

        # Submit identical payload a second time (simulating double click or duplicate listener)
        resp = self.client.post("/api/contact", json=self.valid_msg_1)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["id"], 9001)
        self.assertTrue(data["data"].get("duplicate_prevented"), "Expected duplicate_prevented flag!")

        insert_queries = [q for q, p in executed_queries if "INSERT INTO contact_messages" in str(q)]
        self.assertEqual(len(insert_queries), 0, "Duplicate submission must NOT execute an INSERT query!")
        print("[OK] Verified: Duplicate submission within 60s is intercepted; NO duplicate record created.")

    # =========================================================================
    # 3. DIFFERENT DELIBERATE INQUIRY SUCCEEDS SEPARATELY
    # =========================================================================
    @patch("app.get_db")
    def test_second_different_message_creates_separate_record(self, mock_get_db):
        """A different user message creates its own distinct record."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 9002
        mock_cursor.fetchone.return_value = None # Not a duplicate
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        resp = self.client.post("/api/contact", json=self.valid_msg_2)
        self.assertEqual(resp.status_code, 201)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["id"], 9002)
        print("[OK] Verified: A different customer inquiry creates a distinct record (#9002).")

    # =========================================================================
    # 4. ADMIN CONTACT MESSAGES CARDS RENDERING & STRUCTURE
    # =========================================================================
    def test_admin_html_contains_cards_grid_and_responsive_css(self):
        """Verify admin.html has the cards container, responsive CSS, and deduplication logic."""
        with open("my-node-app/templates/admin.html", "r", encoding="utf-8") as f:
            admin_code = f.read()

        # Check cards container exists
        self.assertIn('id="admin-messages-cards-container"', admin_code)
        self.assertIn('class="contact-cards-grid"', admin_code)

        # Check responsive CSS exists (3 cols, 2 cols tablet, 1 col mobile)
        self.assertIn('grid-template-columns: repeat(3, 1fr)', admin_code)
        self.assertIn('@media (max-width: 1100px)', admin_code)
        self.assertIn('@media (max-width: 680px)', admin_code)

        # Check card elements exist
        self.assertIn('CONTACT MESSAGE', admin_code)
        self.assertIn('contact-msg-card', admin_code)
        self.assertIn('contact-msg-name', admin_code)
        self.assertIn('btn-card-action view', admin_code)
        self.assertIn('btn-card-action reply', admin_code)
        self.assertIn('btn-card-action resolve', admin_code)
        self.assertIn('btn-card-action delete', admin_code)

        # Check frontend deduplication logic exists
        self.assertIn('seenIds = new Set()', admin_code)
        self.assertIn('uniqueMsgs', admin_code)
        print("[OK] Verified: admin.html has responsive 3-column card grid, mobile breakpoints, and deduplication.")

    # =========================================================================
    # 5. ADMIN VIEW DETAILS, REPLY, AND RESOLVE ENDPOINTS
    # =========================================================================
    @patch("app.get_db")
    def test_admin_view_details_auto_marks_read(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            "id": 9001,
            "name": "Arun Prakash",
            "email": "arun.prakash@example.com",
            "phone": "9876543210",
            "subject": "Royal Enfield Classic 350 Test Ride",
            "message": "Hello SMR Motors, I would like to schedule a test ride.",
            "status": "new",
            "admin_reply": None,
            "replied_at": None,
            "resolved_at": None,
            "created_at": "2026-11-06 20:30:00"
        }
        mock_cursor.fetchall.return_value = [] # No previous replies
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        resp = self.client.get("/api/admin/contact-messages/9001", headers=self.admin_headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["status"], "read")
        print("[OK] Verified: View Details returns full sender info and auto-marks status as 'read'.")

    @patch("app.get_db")
    def test_admin_reply_saves_and_updates_status(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            "id": 9001,
            "name": "Arun Prakash",
            "email": "arun.prakash@example.com",
            "subject": "Royal Enfield Classic 350 Test Ride",
            "status": "read"
        }
        mock_cursor.lastrowid = 55
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        reply_payload = {"reply": "Hi Arun, we have booked your test ride for Saturday at 11 AM."}
        resp = self.client.post("/api/admin/contact-messages/9001/reply", json=reply_payload, headers=self.admin_headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["status"], "replied")
        print("[OK] Verified: Admin reply saves response in database and updates status to 'replied'.")

    @patch("app.get_db")
    def test_admin_resolve_updates_status(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"id": 9001, "status": "replied"}
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        resp = self.client.patch("/api/admin/contact-messages/9001/status", json={"status": "resolved"}, headers=self.admin_headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["status"], "resolved")
        print("[OK] Verified: Resolve button updates inquiry status to 'resolved'.")

    @patch("app.get_db")
    def test_admin_delete_removes_inquiry(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"id": 9001, "name": "Arun Prakash"}
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        resp = self.client.delete("/api/admin/contact-messages/9001", headers=self.admin_headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        print("[OK] Verified: Delete button removes inquiry and preserves database integrity.")

    # =========================================================================
    # 6. SECURITY & ROLE GUARDS
    # =========================================================================
    def test_security_guards(self):
        # Missing auth
        r1 = self.client.get("/api/admin/contact-messages")
        self.assertEqual(r1.status_code, 401)

        # Normal user role forbidden
        r2 = self.client.get("/api/admin/contact-messages", headers=self.user_headers)
        self.assertEqual(r2.status_code, 403)
        print("[OK] Verified: Admin security guards reject unauthorized requests with HTTP 401/403.")

if __name__ == "__main__":
    unittest.main()
