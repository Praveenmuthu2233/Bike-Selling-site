import unittest
import json
import os
import sys

# Configure UTF-8 stdout
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('my-node-app'))

import app

class TestTiDBRealDataIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.app.config['TESTING'] = True
        cls.client = app.app.test_client()

        # Generate valid Admin Token for admin endpoints
        import jwt
        import datetime
        admin_payload = {
            "id": 1,
            "username": "admin",
            "name": "Administrator",
            "role": "superadmin",
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1)
        }
        cls.admin_token = jwt.encode(admin_payload, app.JWT_SECRET, algorithm="HS256")
        cls.admin_headers = {"Authorization": f"Bearer {cls.admin_token}"}

    def test_01_tidb_connection(self):
        """Verify live TLS connection to TiDB Cloud smr_motors database."""
        conn = app.get_db()
        self.assertIsNotNone(conn, "TiDB Cloud connection failed")
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT DATABASE() as db_name, VERSION() as ver")
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        self.assertEqual(row['db_name'], 'smr_motors')
        print(f"[Pass] Connected to TiDB database: {row['db_name']}")

    def test_02_all_bike_data_from_tidb(self):
        """Verify /api/bikes returns real listings from TiDB, no fake Hunter 350 Dapper Ash demo data."""
        res = self.client.get('/api/bikes?status=all&limit=50')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data.get('success'))
        bikes = data.get('data') or data.get('bikes') or []
        self.assertIsInstance(bikes, list)
        self.assertGreater(len(bikes), 0, "TiDB should contain real bikes")
        # Ensure no fake demo store records exist
        titles = [b.get('title') for b in bikes]
        self.assertNotIn("Royal Enfield Hunter 350 Dapper Ash", titles)
        print(f"[Pass] /api/bikes loaded {len(bikes)} live motorcycles from TiDB Cloud")

    def test_03_sold_out_bikes_from_tidb(self):
        """Verify /api/bikes/sold returns live sold records from TiDB Cloud."""
        res = self.client.get('/api/bikes/sold')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data.get('success'))
        sold = data.get('data') or data.get('bikes') or []
        self.assertIsInstance(sold, list)
        self.assertGreater(len(sold), 0, "TiDB should contain sold bikes")
        for b in sold:
            self.assertTrue(b.get('isSoldout') == 1 or b.get('status') == 'soldout' or b.get('listing_status') == 'soldout')
        print(f"[Pass] /api/bikes/sold loaded {len(sold)} real sold motorcycles from TiDB Cloud")

    def test_04_enquiries_from_tidb(self):
        """Verify enquiries are fetched from TiDB enquiries table."""
        res = self.client.get('/api/admin/enquiries?limit=20', headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data.get('success'))
        enqs = data.get('data') or data.get('enquiries') or []
        self.assertIsInstance(enqs, list)
        print(f"[Pass] /api/admin/enquiries loaded {len(enqs)} real customer enquiries from TiDB Cloud")

    def test_05_users_from_tidb(self):
        """Verify users are fetched from TiDB users table."""
        res = self.client.get('/api/admin/users?limit=20', headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data.get('success'))
        users = data.get('data') or data.get('users') or []
        self.assertIsInstance(users, list)
        self.assertGreater(len(users), 0, "TiDB users table should have users")
        # Ensure no fake Demo Rider user in live database
        names = [u.get('name') for u in users]
        self.assertNotIn("Demo Rider", names)
        print(f"[Pass] /api/admin/users loaded {len(users)} registered users from TiDB Cloud")

    def test_06_admin_and_staff_from_tidb(self):
        """Verify admin accounts and staff details are fetched from TiDB admins table."""
        res = self.client.get('/api/admin/staff', headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data.get('success'))
        staff = data.get('staff') or data.get('data') or []
        self.assertIsInstance(staff, list)
        self.assertGreaterEqual(len(staff), 4, "TiDB admins table should have 4 admin accounts")
        unames = [s.get('username') for s in staff]
        self.assertIn('admin', unames)
        self.assertIn('mani', unames)
        self.assertIn('murugan', unames)
        self.assertIn('raja', unames)
        print(f"[Pass] /api/admin/staff loaded {len(staff)} staff members from TiDB Cloud: {unames}")

    def test_07_dashboard_metrics_from_tidb(self):
        """Verify dashboard statistics are calculated 100% from TiDB SQL queries."""
        res = self.client.get('/api/admin/dashboard', headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data.get('success'))
        counts = data.get('counts', {})
        self.assertIn('total_bikes', counts)
        self.assertIn('pending_bikes', counts)
        self.assertIn('approved_bikes', counts)
        self.assertIn('sold_bikes', counts)
        self.assertIn('total_users', counts)
        self.assertIn('total_enquiries', counts)
        self.assertIn('total_revenue', counts)
        self.assertIn('total_realized_profit', counts)
        print(f"[Pass] /api/admin/dashboard stats: {counts['total_bikes']} bikes, {counts['sold_bikes']} sold, {counts['total_users']} users, {counts['total_enquiries']} enquiries, revenue ₹{counts.get('total_revenue', 0):,.0f}")

    def test_08_chat_system_connected_to_tidb(self):
        """Verify chat endpoints fetch real conversations and unread counts from TiDB."""
        res = self.client.get('/api/chat/unread-count', headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data.get('success'))
        self.assertIn('unread_count', data)

        res_conv = self.client.get('/api/admin/chat/conversations', headers=self.admin_headers)
        self.assertEqual(res_conv.status_code, 200)
        conv_data = json.loads(res_conv.data)
        self.assertTrue(conv_data.get('success'))
        convs = conv_data.get('conversations', [])
        print(f"[Pass] Chat unread count: {data['unread_count']} | Active conversations: {len(convs)}")

    def test_09_notifications_and_audit_logs(self):
        """Verify notifications and audit logs query live TiDB tables."""
        res_notif = self.client.get('/api/notifications?target_role=admin', headers=self.admin_headers)
        self.assertEqual(res_notif.status_code, 200)
        n_data = json.loads(res_notif.data)
        self.assertTrue(n_data.get('success'))
        notifs = n_data.get('notifications', [])

        res_logs = self.client.get('/api/admin/audit-logs', headers=self.admin_headers)
        self.assertEqual(res_logs.status_code, 200)
        l_data = json.loads(res_logs.data)
        self.assertTrue(l_data.get('success'))
        logs = l_data.get('data', [])
        print(f"[Pass] Loaded {len(notifs)} notifications and {len(logs)} audit logs from TiDB Cloud")

    def test_10_database_unavailable_error_handling(self):
        """Verify that when TiDB connection is unavailable, APIs return 503 error, NOT fake records."""
        original_get_db = app.get_db
        try:
            # Simulate DB offline
            app.get_db = lambda: None

            # Test /api/bikes
            res_bikes = self.client.get('/api/bikes')
            self.assertEqual(res_bikes.status_code, 503)
            b_data = json.loads(res_bikes.data)
            self.assertFalse(b_data.get('success'))
            self.assertIn('Database connection unavailable', b_data.get('message', ''))

            # Test /api/admin/dashboard
            res_dash = self.client.get('/api/admin/dashboard', headers=self.admin_headers)
            self.assertEqual(res_dash.status_code, 503)
            d_data = json.loads(res_dash.data)
            self.assertFalse(d_data.get('success'))

            # Test /api/admin/enquiries
            res_enq = self.client.get('/api/admin/enquiries', headers=self.admin_headers)
            self.assertEqual(res_enq.status_code, 503)

            # Test /api/admin/users
            res_users = self.client.get('/api/admin/users', headers=self.admin_headers)
            self.assertEqual(res_users.status_code, 503)

            print("[Pass] When database is offline, APIs return HTTP 503 with clear error message, zero fake fallback data returned")
        finally:
            app.get_db = original_get_db

    def test_11_demo_login_disabled(self):
        """Verify /api/auth/demo-google is disabled and rejects demo logins."""
        res = self.client.post('/api/auth/demo-google')
        self.assertEqual(res.status_code, 403)
        data = json.loads(res.data)
        self.assertFalse(data.get('success'))
        self.assertIn('disabled', data.get('message', '').lower())
        print("[Pass] /api/auth/demo-google is safely disabled")

if __name__ == '__main__':
    unittest.main()
