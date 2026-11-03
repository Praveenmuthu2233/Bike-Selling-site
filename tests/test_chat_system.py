import unittest
import json
import os
import sys
import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_DIR = os.path.join(BASE_DIR, "my-node-app")
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from app import app, JWT_SECRET, get_db
import jwt

class RealTimeCustomerAdminChatTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = app.test_client()
        cls.app.testing = True

        now = datetime.datetime.now(datetime.timezone.utc)
        # Superadmin token
        cls.superadmin_token = jwt.encode({
            'admin_id': 1,
            'username': 'super_chat_tester',
            'role': 'superadmin',
            'exp': now + datetime.timedelta(hours=2)
        }, JWT_SECRET, algorithm='HS256')

        # Admin / Staff token
        cls.admin_token = jwt.encode({
            'admin_id': 2,
            'username': 'staff_chat_tester',
            'role': 'admin',
            'exp': now + datetime.timedelta(hours=2)
        }, JWT_SECRET, algorithm='HS256')

        # User A token
        cls.user_a_id = 9101
        cls.user_a_token = jwt.encode({
            'user_id': cls.user_a_id,
            'email': 'customer_a@example.com',
            'name': 'Praveen Customer',
            'role': 'user',
            'exp': now + datetime.timedelta(hours=2)
        }, JWT_SECRET, algorithm='HS256')

        # User B token (for unauthorized cross-tenant testing)
        cls.user_b_id = 9102
        cls.user_b_token = jwt.encode({
            'user_id': cls.user_b_id,
            'email': 'intruder_b@example.com',
            'name': 'Intruder User',
            'role': 'user',
            'exp': now + datetime.timedelta(hours=2)
        }, JWT_SECRET, algorithm='HS256')

        # Ensure User A and User B exist in users table
        conn = get_db()
        if conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO users (id, name, email, role)
                VALUES (%s, 'Praveen Customer', 'customer_a@example.com', 'user')
                ON DUPLICATE KEY UPDATE name=VALUES(name)
            """, (cls.user_a_id,))
            cur.execute("""
                INSERT INTO users (id, name, email, role)
                VALUES (%s, 'Intruder User', 'intruder_b@example.com', 'user')
                ON DUPLICATE KEY UPDATE name=VALUES(name)
            """, (cls.user_b_id,))

            # Find a bike to link
            cur.execute("SELECT id FROM bikes WHERE isSoldout = 0 ORDER BY id DESC LIMIT 1")
            bike_row = cur.fetchone()
            cls.test_bike_id = bike_row[0] if bike_row else None

            # Clean any previous test run chat data for test users
            cur.execute("DELETE FROM chat_messages WHERE sender_id IN (%s, %s)", (cls.user_a_id, cls.user_b_id))
            cur.execute("DELETE FROM chat_read_status WHERE user_id IN (%s, %s)", (cls.user_a_id, cls.user_b_id))
            cur.execute("DELETE FROM chat_conversations WHERE user_id IN (%s, %s)", (cls.user_a_id, cls.user_b_id))

            conn.commit()
            cur.close()
            conn.close()

    def test_01_user_creates_conversation_persists_in_tidb(self):
        """User creates a conversation with a bike link; verifies TiDB persistence."""
        headers = {'Authorization': f'Bearer {self.user_a_token}'}
        payload = {
            "subject": "Inquiry regarding Royal Enfield Hunter 350",
            "bike_id": self.test_bike_id,
            "message": "Hello, is this motorcycle available for inspection and test ride this Saturday?"
        }
        res = self.app.post('/api/chat/conversations', data=json.dumps(payload), content_type='application/json', headers=headers)
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        conv_id = data.get("conversation_id")
        self.assertIsNotNone(conv_id)
        RealTimeCustomerAdminChatTest.created_conv_id = conv_id

        # Direct TiDB check
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM chat_conversations WHERE id = %s", (conv_id,))
        conv = cur.fetchone()
        self.assertIsNotNone(conv)
        self.assertEqual(conv["user_id"], self.user_a_id)
        self.assertEqual(conv["status"], "open")
        self.assertEqual(conv["bike_id"], self.test_bike_id)

        # Check initial message in chat_messages
        cur.execute("SELECT * FROM chat_messages WHERE conversation_id = %s", (conv_id,))
        msgs = cur.fetchall()
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]["sender_id"], self.user_a_id)
        self.assertEqual(msgs[0]["sender_role"], "user")
        self.assertIn("available for inspection", msgs[0]["message"])
        self.assertEqual(msgs[0]["is_read"], 0)

        cur.close()
        conn.close()

    def test_02_user_lists_conversations(self):
        """User fetches conversation list; verifies metadata and unread counts."""
        headers = {'Authorization': f'Bearer {self.user_a_token}'}
        res = self.app.get('/api/chat/conversations', headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        convs = data.get("conversations", [])
        self.assertGreaterEqual(len(convs), 1)

        target = next((c for c in convs if c["id"] == self.created_conv_id), None)
        self.assertIsNotNone(target)
        self.assertEqual(target["subject"], "Inquiry regarding Royal Enfield Hunter 350")
        self.assertEqual(target["status"], "open")
        self.assertEqual(target["last_sender_role"], "user")

    def test_03_admin_lists_conversations_with_filters(self):
        """Admin views conversations, tests status filter and search query."""
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        res = self.app.get('/api/admin/chat/conversations?filter=open&search=Praveen', headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        convs = data.get("conversations", [])
        self.assertGreaterEqual(len(convs), 1)
        target = next((c for c in convs if c["id"] == self.created_conv_id), None)
        self.assertIsNotNone(target)
        self.assertGreaterEqual(target["unread_count"], 1)

    def test_04_admin_replies_to_customer(self):
        """Admin sends reply; verifies DB persistence and notification trigger."""
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        payload = {
            "message": "Yes, Mr. Praveen! The motorcycle is in pristine showroom condition and available for test ride on Saturday at 11 AM."
        }
        res = self.app.post(f'/api/chat/conversations/{self.created_conv_id}/messages',
                            data=json.dumps(payload),
                            content_type='application/json',
                            headers=headers)
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        reply_msg_id = data["message"]["id"]
        RealTimeCustomerAdminChatTest.admin_msg_id = reply_msg_id

        # Verify in TiDB
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM chat_messages WHERE id = %s", (reply_msg_id,))
        msg = cur.fetchone()
        self.assertIsNotNone(msg)
        self.assertEqual(msg["sender_role"], "admin")
        self.assertEqual(msg["is_read"], 0)
        cur.close()
        conn.close()

    def test_05_user_fetches_messages_and_read_receipt_updates(self):
        """User fetches messages; marks admin message as read in TiDB."""
        headers = {'Authorization': f'Bearer {self.user_a_token}'}
        res = self.app.get(f'/api/chat/conversations/{self.created_conv_id}/messages', headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        msgs = data.get("messages", [])
        self.assertGreaterEqual(len(msgs), 2)

        # Check in TiDB that admin message was marked as read
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT is_read FROM chat_messages WHERE id = %s", (self.admin_msg_id,))
        row = cur.fetchone()
        self.assertEqual(row["is_read"], 1)
        cur.close()
        conn.close()

    def test_06_delta_polling_since_id(self):
        """Real-time delta polling: only messages newer than since_id are returned."""
        headers = {'Authorization': f'Bearer {self.user_a_token}'}
        # First message ID is 1 or previous; if we pass admin_msg_id - 1, we should get admin_msg_id
        res = self.app.get(f'/api/chat/conversations/{self.created_conv_id}/messages?since_id={self.admin_msg_id - 1}', headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        msgs = data.get("messages", [])
        ids = [m["id"] for m in msgs]
        self.assertIn(self.admin_msg_id, ids)

        # Passing admin_msg_id as since_id should return 0 new messages
        res2 = self.app.get(f'/api/chat/conversations/{self.created_conv_id}/messages?since_id={self.admin_msg_id}', headers=headers)
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(len(res2.get_json().get("messages", [])), 0)

    def test_07_strict_security_user_cannot_access_other_users_chat(self):
        """Security isolation: User B cannot view or send to User A's conversation."""
        headers_b = {'Authorization': f'Bearer {self.user_b_token}'}

        # Attempt to read User A's conversation
        res_read = self.app.get(f'/api/chat/conversations/{self.created_conv_id}/messages', headers=headers_b)
        self.assertEqual(res_read.status_code, 403)
        self.assertIn("Access forbidden", res_read.get_json().get("message", ""))

        # Attempt to send to User A's conversation
        res_send = self.app.post(f'/api/chat/conversations/{self.created_conv_id}/messages',
                                 data=json.dumps({"message": "I am an unauthorized intruder."}),
                                 content_type='application/json',
                                 headers=headers_b)
        self.assertEqual(res_send.status_code, 403)

    def test_08_unauthenticated_request_rejected(self):
        """Unauthenticated requests must be rejected with 401."""
        res = self.app.get(f'/api/chat/conversations/{self.created_conv_id}/messages')
        self.assertEqual(res.status_code, 401)

    def test_09_admin_resolves_and_user_reopens_conversation(self):
        """Admin marks resolved; User sending follow-up automatically reopens to 'open'."""
        admin_headers = {'Authorization': f'Bearer {self.admin_token}'}
        res_res = self.app.put(f'/api/admin/chat/conversations/{self.created_conv_id}/status',
                               data=json.dumps({"status": "resolved"}),
                               content_type='application/json',
                               headers=admin_headers)
        self.assertEqual(res_res.status_code, 200)

        # Check status is resolved in TiDB
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT status FROM chat_conversations WHERE id = %s", (self.created_conv_id,))
        self.assertEqual(cur.fetchone()["status"], "resolved")
        cur.close()
        conn.close()

        # User sends a follow-up
        user_headers = {'Authorization': f'Bearer {self.user_a_token}'}
        res_follow = self.app.post(f'/api/chat/conversations/{self.created_conv_id}/messages',
                                   data=json.dumps({"message": "One more question: do you have RC transfer assistance?"}),
                                   content_type='application/json',
                                   headers=user_headers)
        self.assertEqual(res_follow.status_code, 201)

        # Check status reopened to 'open' in TiDB on fresh connection
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT status FROM chat_conversations WHERE id = %s", (self.created_conv_id,))
        self.assertEqual(cur.fetchone()["status"], "open")
        cur.close()
        conn.close()

    def test_10_input_validation(self):
        """Rejects empty messages and messages exceeding 2000 chars."""
        headers = {'Authorization': f'Bearer {self.user_a_token}'}

        # Empty message
        res_empty = self.app.post(f'/api/chat/conversations/{self.created_conv_id}/messages',
                                  data=json.dumps({"message": "   "}),
                                  content_type='application/json',
                                  headers=headers)
        self.assertEqual(res_empty.status_code, 400)

        # Giant message (2500 chars)
        res_giant = self.app.post(f'/api/chat/conversations/{self.created_conv_id}/messages',
                                  data=json.dumps({"message": "A" * 2500}),
                                  content_type='application/json',
                                  headers=headers)
        self.assertEqual(res_giant.status_code, 400)

    def test_11_financial_privacy_protected_in_chat(self):
        """Conversations return public price but NEVER expose dealer buying price or margin."""
        headers = {'Authorization': f'Bearer {self.user_a_token}'}
        res = self.app.get(f'/api/chat/conversations/{self.created_conv_id}/messages', headers=headers)
        self.assertEqual(res.status_code, 200)
        bike_data = res.get_json().get("conversation", {})
        self.assertNotIn("buying_price", bike_data)
        self.assertNotIn("realized_profit", bike_data)
        self.assertNotIn("seller_payout", bike_data)

    def test_12_superadmin_staff_assignment(self):
        """Superadmin can assign conversation to staff; regular admin cannot."""
        super_headers = {'Authorization': f'Bearer {self.superadmin_token}'}
        res = self.app.put(f'/api/admin/chat/conversations/{self.created_conv_id}/assign',
                           data=json.dumps({"assigned_admin_id": 2}),
                           content_type='application/json',
                           headers=super_headers)
        self.assertEqual(res.status_code, 200)

        # Verify in TiDB
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT assigned_admin_id FROM chat_conversations WHERE id = %s", (self.created_conv_id,))
        self.assertEqual(cur.fetchone()["assigned_admin_id"], 2)
        cur.close()
        conn.close()

if __name__ == '__main__':
    unittest.main()
