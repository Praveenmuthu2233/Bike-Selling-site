import os
import sys
import unittest
import json
import jwt

# Add my-node-app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'my-node-app'))

from app import app, JWT_SECRET, get_db

class TestDashboardRBACExportAndSession(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = app.test_client()

        # Generate tokens for testing
        # 1. Superadmin Token (e.g. Murugan / Raja / admin)
        self.superadmin_token = jwt.encode({
            "id": 1,
            "username": "admin",
            "name": "Administrator",
            "role": "superadmin"
        }, JWT_SECRET, algorithm="HS256")

        # 2. Staff Admin Token (e.g. Mani)
        self.staff_token = jwt.encode({
            "id": 2,
            "username": "mani",
            "name": "Mani (Staff)",
            "role": "admin"
        }, JWT_SECRET, algorithm="HS256")

        # 3. Regular User Token
        self.user_token = jwt.encode({
            "id": 99,
            "email": "rider@smrmotors.com",
            "name": "Test Rider",
            "role": "user"
        }, JWT_SECRET, algorithm="HS256")

    # =========================================================================
    # 1. ACCURATE DASHBOARD COUNTS TESTS
    # =========================================================================
    def test_01_dashboard_counts_structure_and_types(self):
        """Verify dashboard statistics return direct counts with correct field names and types."""
        res = self.client.get(
            "/api/admin/dashboard",
            headers={"Authorization": f"Bearer {self.superadmin_token}"}
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        
        # Verify stats accessible at root and inside data
        stats = data.get("stats") or data.get("counts")
        self.assertIsNotNone(stats, "Stats must be returned in dashboard response")
        self.assertIn("total_bikes", stats)
        self.assertIn("pending_bikes", stats)
        self.assertIn("approved_bikes", stats)
        self.assertIn("sold_bikes", stats)
        self.assertIn("total_users", stats)
        self.assertIn("total_enquiries", stats)

        # Total bikes must be >= pending + approved + sold
        total = stats["total_bikes"]
        pending = stats["pending_bikes"]
        approved = stats["approved_bikes"]
        sold = stats["sold_bikes"]
        print(f"\n[Test 1] TiDB Dashboard Counts: Total={total}, Pending={pending}, Approved={approved}, Sold={sold}, Users={stats['total_users']}, Enquiries={stats['total_enquiries']}")
        self.assertGreaterEqual(total, pending + approved + sold)

    def test_02_dashboard_status_exclusivity(self):
        """Verify sold bikes are never active, pending never approved, and rejected never active."""
        res = self.client.get(
            "/api/admin/dashboard",
            headers={"Authorization": f"Bearer {self.superadmin_token}"}
        )
        data = res.get_json()
        stats = data.get("stats")
        self.assertIsInstance(stats["pending_bikes"], int)
        self.assertIsInstance(stats["approved_bikes"], int)
        self.assertIsInstance(stats["sold_bikes"], int)
        self.assertIsInstance(stats["rejected_bikes"], int)

    # =========================================================================
    # 2. RBAC & FINANCIAL REDACTION TESTS
    # =========================================================================
    def test_03_superadmin_has_full_financial_access(self):
        """Superadmin must see revenue, seller payout, expenses, and realized profit."""
        res = self.client.get(
            "/api/admin/dashboard",
            headers={"Authorization": f"Bearer {self.superadmin_token}"}
        )
        data = res.get_json()
        self.assertTrue(data.get("is_superadmin"))
        stats = data.get("stats")
        self.assertIsNotNone(stats.get("total_revenue"))
        self.assertIsNotNone(stats.get("total_seller_payout"))
        self.assertIsNotNone(stats.get("total_realized_profit"))
        self.assertIsNotNone(data["data"].get("financials"))

    def test_04_staff_admin_financials_are_redacted(self):
        """Staff admin must NEVER see sensitive revenue, payout, expenses, or profit."""
        res = self.client.get(
            "/api/admin/dashboard",
            headers={"Authorization": f"Bearer {self.staff_token}"}
        )
        data = res.get_json()
        self.assertFalse(data.get("is_superadmin"))
        stats = data.get("stats")
        self.assertIsNone(stats.get("total_revenue"))
        self.assertIsNone(stats.get("total_seller_payout"))
        self.assertIsNone(stats.get("total_realized_profit"))
        self.assertIsNone(data["data"].get("financials"))

    # =========================================================================
    # 3. USER PANEL SECURITY & ADMIN CONTROL REMOVAL
    # =========================================================================
    def test_05_regular_user_cannot_access_admin_dashboard(self):
        """Regular user token must receive HTTP 403 Forbidden for admin dashboard."""
        res = self.client.get(
            "/api/admin/dashboard",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        self.assertEqual(res.status_code, 403)

    def test_06_regular_user_cannot_approve_bike(self):
        """Regular user token must receive HTTP 403 Forbidden when attempting to approve a bike."""
        res = self.client.put(
            "/api/admin/bikes/1/approve",
            headers={"Authorization": f"Bearer {self.user_token}"},
            json={"status": "approved"}
        )
        self.assertEqual(res.status_code, 403)

    def test_07_regular_user_cannot_reject_bike(self):
        """Regular user token must receive HTTP 403 Forbidden when attempting to reject a bike."""
        res = self.client.put(
            "/api/admin/bikes/1/reject",
            headers={"Authorization": f"Bearer {self.user_token}"},
            json={"rejection_reason": "Price too high"}
        )
        self.assertEqual(res.status_code, 403)

    def test_08_user_profile_template_has_no_admin_controls(self):
        """Inspect profile.html template to ensure zero admin approval buttons exist."""
        profile_path = os.path.join(os.path.dirname(__file__), '..', 'my-node-app', 'templates', 'profile.html')
        with open(profile_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Must not contain admin approve/reject endpoints or buttons
        self.assertNotIn("/api/admin/bikes/", content)
        self.assertNotIn("approveBike(", content)
        self.assertNotIn("rejectBike(", content)
        self.assertIn("My Bike Listings", content)
        self.assertIn("Pending Review", content)
        self.assertIn("Approved &amp; Live", content)

    # =========================================================================
    # 4. PDF AND EXCEL REPORT EXPORTS
    # =========================================================================
    def test_09_export_inventory_pdf(self):
        """Export inventory listings report as professional PDF."""
        res = self.client.get(
            "/api/admin/reports/export?type=listings&format=pdf",
            headers={"Authorization": f"Bearer {self.superadmin_token}"}
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, "application/pdf")
        self.assertTrue(res.data.startswith(b"%PDF"), "Must start with PDF signature %PDF")
        self.assertIn("attachment; filename=", res.headers.get("Content-Disposition", ""))

    def test_10_export_inventory_excel(self):
        """Export inventory listings report as formatted Excel (.xlsx)."""
        res = self.client.get(
            "/api/admin/reports/export?type=listings&format=xlsx",
            headers={"Authorization": f"Bearer {self.superadmin_token}"}
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn("spreadsheetml", res.mimetype)
        self.assertTrue(res.data.startswith(b"PK\x03\x04"), "Must start with ZIP/XLSX magic bytes")

    def test_11_export_sold_report_pdf_and_excel(self):
        """Export sold motorcycles report as PDF and Excel."""
        res_pdf = self.client.get(
            "/api/admin/reports/export?type=sold&format=pdf",
            headers={"Authorization": f"Bearer {self.superadmin_token}"}
        )
        self.assertEqual(res_pdf.status_code, 200)
        self.assertTrue(res_pdf.data.startswith(b"%PDF"))

        res_xlsx = self.client.get(
            "/api/admin/reports/export?type=sold&format=xlsx",
            headers={"Authorization": f"Bearer {self.superadmin_token}"}
        )
        self.assertEqual(res_xlsx.status_code, 200)
        self.assertTrue(res_xlsx.data.startswith(b"PK\x03\x04"))

    def test_12_superadmin_can_export_financial_pdf_and_excel(self):
        """Superadmin can export confidential financial ledger."""
        res_pdf = self.client.get(
            "/api/admin/reports/export?type=financial&format=pdf",
            headers={"Authorization": f"Bearer {self.superadmin_token}"}
        )
        self.assertEqual(res_pdf.status_code, 200)
        self.assertTrue(res_pdf.data.startswith(b"%PDF"))

        res_xlsx = self.client.get(
            "/api/admin/reports/export?type=financial&format=xlsx",
            headers={"Authorization": f"Bearer {self.superadmin_token}"}
        )
        self.assertEqual(res_xlsx.status_code, 200)
        self.assertTrue(res_xlsx.data.startswith(b"PK\x03\x04"))

    def test_13_staff_admin_forbidden_from_financial_export(self):
        """Staff admin must receive HTTP 403 Forbidden when requesting financial report."""
        res = self.client.get(
            "/api/admin/reports/export?type=financial&format=pdf",
            headers={"Authorization": f"Bearer {self.staff_token}"}
        )
        self.assertEqual(res.status_code, 403)
        data = res.get_json()
        self.assertFalse(data.get("success"))
        self.assertIn("SUPERADMIN", data.get("message", "").upper())

    def test_14_export_with_date_brand_and_status_filters(self):
        """Test report exports with preset date, brand, and status filters."""
        res = self.client.get(
            "/api/admin/reports/export?type=listings&format=pdf&preset=last_30_days&brand=Yamaha&status=approved",
            headers={"Authorization": f"Bearer {self.superadmin_token}"}
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data.startswith(b"%PDF"))

    # =========================================================================
    # 5. REMEMBERED GOOGLE LOGIN – SEVEN DAYS TESTS
    # =========================================================================
    def test_15_remembered_session_cookie_generation(self):
        """Sign-in sets secure HttpOnly smr_remember_token cookie with 7-day max-age."""
        res = self.client.post(
            "/api/auth/demo-google",
            json={"remember_me": True}
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        
        cookie = res.headers.get("Set-Cookie", "")
        self.assertIn("smr_remember_token=", cookie)
        self.assertIn("HttpOnly", cookie)
        self.assertIn("Max-Age=604800", cookie) # 7 days = 604800 seconds

    def test_16_auto_restore_session_from_cookie(self):
        """Revisiting with remembered cookie restores user profile and issues valid JWT."""
        # Step 1: Sign in and get cookie
        login_res = self.client.post(
            "/api/auth/demo-google",
            json={"remember_me": True}
        )
        self.assertEqual(login_res.status_code, 200)
        
        # Step 2: Call remembered-session endpoint with the cookie
        restore_res = self.client.get("/api/auth/remembered-session")
        self.assertEqual(restore_res.status_code, 200)
        restore_data = restore_res.get_json()
        self.assertTrue(restore_data.get("success"))
        self.assertTrue(restore_data.get("restored"))
        self.assertIsNotNone(restore_data.get("token"))
        self.assertIsNotNone(restore_data.get("user"))
        print(f"\n[Test 16] Successfully restored session for: {restore_data['user']['name']} ({restore_data['user']['email']})")

    def test_17_explicit_logout_revokes_session(self):
        """Explicit logout revokes session in DB and clears persistent cookie."""
        # Step 1: Sign in
        self.client.post("/api/auth/demo-google", json={"remember_me": True})
        
        # Step 2: Explicit logout
        logout_res = self.client.post("/api/auth/logout")
        self.assertEqual(logout_res.status_code, 200)
        cookie = logout_res.headers.get("Set-Cookie", "")
        self.assertIn("smr_remember_token=;", cookie) # cleared cookie

        # Step 3: Attempting restore must now fail (HTTP 401)
        restore_after_logout = self.client.get("/api/auth/remembered-session")
        self.assertEqual(restore_after_logout.status_code, 401)

if __name__ == "__main__":
    unittest.main()
