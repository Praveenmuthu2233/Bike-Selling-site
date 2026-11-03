import os
import sys
import unittest
import json
import datetime
import jwt

# Add my-node-app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "my-node-app"))

from app import app, JWT_SECRET, get_db

class TestProfilePrivacyFooter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        cls.client = app.test_client()

        # Seed test user token
        cls.user_payload = {
            "id": 1,
            "email": "rider.karthik@example.com",
            "name": "Karthik Raja",
            "role": "user",
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
        }
        cls.user_token = jwt.encode(cls.user_payload, JWT_SECRET, algorithm="HS256")

        # Seed superadmin token
        cls.admin_payload = {
            "id": 1,
            "username": "admin",
            "name": "Administrator",
            "role": "superadmin",
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
        }
        cls.admin_token = jwt.encode(cls.admin_payload, JWT_SECRET, algorithm="HS256")

    def test_01_user_profile_routes_and_aliases(self):
        """Verify all user profile and dashboard URL aliases return 200 OK."""
        aliases = [
            "/profile",
            "/profile.html",
            "/user/profile",
            "/user/profile.html",
            "/user/dashboard",
            "/user/dashboard.html",
            "/dashboard",
            "/dashboard.html"
        ]
        for route in aliases:
            res = self.client.get(route)
            self.assertEqual(res.status_code, 200, f"Route {route} failed with {res.status_code}")
            self.assertIn("Rider Overview", res.get_data(as_text=True))
        print("[PASS] Test 01: All User Profile & Dashboard route aliases verified.")

    def test_02_privacy_policy_page_content_and_footer(self):
        """Verify Privacy Policy page loads with all mandatory sections, contact info & footer."""
        for route in ["/privacy", "/privacy.html", "/privacy-policy", "/privacy-policy.html"]:
            res = self.client.get(route)
            self.assertEqual(res.status_code, 200, f"Privacy route {route} failed")
            html = res.get_data(as_text=True)

            # Check core sections
            self.assertIn("Privacy Policy & Data Rights", html)
            self.assertIn("Introduction", html)
            self.assertIn("Information We Collect", html)
            self.assertIn("Personal Information", html)
            self.assertIn("Google Account Authentication", html)
            self.assertIn("Bike Listing Information", html)
            self.assertIn("Customer Enquiries", html)
            self.assertIn("Uploaded Images", html)
            self.assertIn("How We Use Information", html)
            self.assertIn("Database Storage and Security", html)
            self.assertIn("Third-Party Services", html)
            self.assertIn("Cookies and Sessions", html)
            self.assertIn("Data Retention", html)
            self.assertIn("User Rights", html)
            self.assertIn("Account Deletion Requests", html)
            self.assertIn("Children's Privacy", html)
            self.assertIn("Policy Updates", html)
            self.assertIn("Contact Information", html)

            # Check footer requirements
            self.assertIn("SMR MOTORS", html)
            self.assertIn("Verified Pre-Owned Motorcycles Marketplace", html)
            self.assertIn("praveenmuthu9500@gmail.com", html)
            self.assertIn("9:30 AM – 8:30 PM", html)
            self.assertIn("2026 SMR Motors. All Rights Reserved.", html)
        print("[PASS] Test 02: Privacy Policy page content and professional footer verified.")

    def test_03_disclaimer_page_content_and_footer(self):
        """Verify Disclaimer page loads with marketplace intermediary statements and safe practices."""
        for route in ["/disclaimer", "/disclaimer.html"]:
            res = self.client.get(route)
            self.assertEqual(res.status_code, 200, f"Disclaimer route {route} failed")
            html = res.get_data(as_text=True)

            self.assertIn("Platform Disclaimer & Notice", html)
            self.assertIn("Marketplace & Intermediary Capacity", html)
            self.assertIn("Seller-Provided Specifications", html)
            self.assertIn("Physical Vehicle Inspection", html)
            self.assertIn("Documentation, RC Transfer", html)
            self.assertIn("Pricing Variations & Inventory Availability", html)
            self.assertIn("Limitation of Liability", html)
            self.assertIn("praveenmuthu9500@gmail.com", html)
            self.assertIn("2026 SMR Motors. All Rights Reserved.", html)
        print("[PASS] Test 03: Disclaimer page advisory clauses and footer links verified.")

    def test_04_privacy_request_api(self):
        """Verify POST /api/privacy/request handles account deletion & data export requests."""
        # Test validation failure
        res_fail = self.client.post("/api/privacy/request", json={"name": "", "email": ""})
        self.assertEqual(res_fail.status_code, 400)

        # Test valid submission
        payload = {
            "name": "Karthik Raja",
            "email": "karthik.raja@example.com",
            "phone": "+91 9840123456",
            "request_type": "account_deletion",
            "details": "Please permanently remove my account and phone number."
        }
        res_ok = self.client.post("/api/privacy/request", json=payload)
        self.assertEqual(res_ok.status_code, 201)
        data = res_ok.get_json()
        self.assertTrue(data["success"])
        self.assertIn("reference #", data["message"])
        print("[PASS] Test 04: Privacy and account deletion request API verified.")

    def test_05_auth_me_and_session_persistence(self):
        """Verify JWT session verification for users and rejection of unauthenticated requests."""
        # Unauthenticated request
        res_unauth = self.client.get("/api/auth/me")
        self.assertEqual(res_unauth.status_code, 401)

        # Authenticated user request
        res_auth = self.client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        self.assertEqual(res_auth.status_code, 200)
        user_data = res_auth.get_json()["user"]
        self.assertEqual(user_data["id"], 1)
        self.assertTrue(user_data.get("email"))
        print("[PASS] Test 05: /api/auth/me session validation & user persistence verified.")

    def test_06_role_separation_user_vs_admin(self):
        """Verify normal users cannot access admin telemetry while admins access their portal."""
        # User trying to access admin dashboard endpoint (Must fail with 403 Forbidden)
        user_res = self.client.get(
            "/api/admin/dashboard",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        self.assertEqual(user_res.status_code, 403)

        # Superadmin accessing admin dashboard endpoint
        admin_res = self.client.get(
            "/api/admin/dashboard",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        self.assertEqual(admin_res.status_code, 200)

        # Admin page alias
        admin_page_res = self.client.get("/admin/dashboard.html")
        self.assertEqual(admin_page_res.status_code, 200)
        print("[PASS] Test 06: Role-based separation (User vs Admin Console) verified.")

if __name__ == "__main__":
    unittest.main()
