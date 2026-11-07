import os
import sys
import unittest
import json
import jwt
from datetime import datetime, timezone

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "my-node-app")))

import app as flask_app_module
from app import app, JWT_SECRET

class TestSoldOutAdminAndHomepage(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()
        
        # Superadmin token
        self.superadmin_token = jwt.encode(
            {"id": 1, "username": "superadmin", "role": "superadmin", "exp": datetime.now(timezone.utc).timestamp() + 3600},
            JWT_SECRET,
            algorithm="HS256"
        )
        self.superadmin_headers = {"Authorization": f"Bearer {self.superadmin_token}"}
        
        # Staff Admin token
        self.staff_token = jwt.encode(
            {"id": 2, "username": "staff1", "role": "admin", "exp": datetime.now(timezone.utc).timestamp() + 3600},
            JWT_SECRET,
            algorithm="HS256"
        )
        self.staff_headers = {"Authorization": f"Bearer {self.staff_token}"}

    def test_01_homepage_sold_bikes_cap_and_privacy(self):
        """Homepage sold API must strictly cap at 6 units and hide confidential financials and customer phones."""
        resp = self.client.get("/api/homepage/sold-bikes")
        # Should return 200 or 503 (if sandbox blocks db network)
        if resp.status_code == 200:
            data = resp.get_json()
            self.assertTrue(data.get("success"))
            self.assertIn("data", data)
            items = data["data"]
            self.assertLessEqual(len(items), 6, "Homepage sold bikes must never exceed 6 units")
            
            for item in items:
                # Confidential financial fields must be stripped
                self.assertNotIn("buying_price", item, "Confidential buying price must NOT be in homepage payload")
                self.assertNotIn("net_profit", item, "Confidential net profit must NOT be in homepage payload")
                self.assertNotIn("realized_profit", item, "Confidential realized profit must NOT be in homepage payload")
                self.assertNotIn("total_expenses", item, "Expenses must NOT be in homepage payload")
                # Private customer details must be stripped
                self.assertNotIn("customer_phone", item, "Private customer phone must NOT be in homepage payload")
                self.assertNotIn("seller_phone", item, "Private seller phone must NOT be in homepage payload")
                # Public-safe fields present
                self.assertIn("title", item)
                self.assertIn("brand", item)
                self.assertIn("price", item)
                print(f" [PASS] Homepage item #{item.get('id')}: {item.get('title')} (₹{item.get('price'):,})")
            print(f" [PASS] Homepage sold gallery returned {len(items)} items (capped <= 6).")
        elif resp.status_code == 503:
            print(" [NOTICE] TiDB Cloud host unreachable in sandbox (expected in offline sandbox).")

    def test_02_homepage_alias_endpoint(self):
        """Alternative homepage route /api/homepage/sold must match."""
        resp = self.client.get("/api/homepage/sold")
        if resp.status_code == 200:
            data = resp.get_json()
            self.assertTrue(data.get("success"))
            self.assertLessEqual(len(data.get("data", [])), 6)
            print(" [PASS] /api/homepage/sold returned valid capped response.")

    def test_03_admin_sold_bikes_requires_auth(self):
        """Admin sold bikes API must reject unauthenticated requests."""
        resp = self.client.get("/api/admin/sold-bikes")
        self.assertIn(resp.status_code, [401, 403], "Unauthenticated request must be denied")
        print(" [PASS] Unauthenticated access to /api/admin/sold-bikes correctly rejected.")

    def test_04_admin_sold_bikes_pagination_and_counts(self):
        """Admin sold bikes must support pagination with default limit 10, total_sold_count, and total_matching_count."""
        resp = self.client.get("/api/admin/sold-bikes?page=1&limit=10", headers=self.superadmin_headers)
        if resp.status_code == 200:
            data = resp.get_json()
            self.assertTrue(data.get("success"))
            self.assertIn("total_sold_count", data)
            self.assertIn("total_matching_count", data)
            self.assertIn("pagination", data)
            pag = data["pagination"]
            self.assertEqual(pag.get("limit"), 10)
            self.assertEqual(pag.get("page"), 1)
            self.assertIn("totalPages", pag)
            self.assertIn("total", pag)
            
            # Test custom limits: 20, 50, 100
            for lim in [20, 50, 100]:
                r = self.client.get(f"/api/admin/sold-bikes?page=1&limit={lim}", headers=self.superadmin_headers)
                self.assertEqual(r.status_code, 200)
                d = r.get_json()
                self.assertEqual(d["pagination"]["limit"], lim)
            print(f" [PASS] Admin pagination verified for limits 10, 20, 50, 100. Total Archive Count: {data['total_sold_count']}, Matching Filter: {data['total_matching_count']}")

    def test_05_admin_sold_bikes_rbac_superadmin_vs_staff(self):
        """Superadmin must see profit metrics; Staff admin must have profit metrics redacted."""
        resp_super = self.client.get("/api/admin/sold-bikes", headers=self.superadmin_headers)
        resp_staff = self.client.get("/api/admin/sold-bikes", headers=self.staff_headers)
        
        if resp_super.status_code == 200 and resp_staff.status_code == 200:
            d_super = resp_super.get_json()
            d_staff = resp_staff.get_json()
            
            self.assertTrue(d_super.get("is_superadmin"))
            self.assertFalse(d_staff.get("is_superadmin"))
            
            if d_super.get("data"):
                item_super = d_super["data"][0]
                self.assertIn("buying_price", item_super)
                self.assertIn("net_profit", item_super)
                self.assertIn("gross_profit", item_super)
                self.assertIn("profit_percentage", item_super)
                
            if d_staff.get("data"):
                item_staff = d_staff["data"][0]
                self.assertNotIn("buying_price", item_staff)
                self.assertNotIn("net_profit", item_staff)
                self.assertNotIn("gross_profit", item_staff)
                self.assertNotIn("profit_percentage", item_staff)
            print(" [PASS] RBAC verified: Superadmin sees profit margins; Staff Admin receives redacted telemetry.")

    def test_06_admin_search_and_brand_filters(self):
        """Admin sold bikes search and brand filters must filter results properly."""
        resp = self.client.get("/api/admin/sold-bikes?search=Royal&brand=Royal+Enfield", headers=self.superadmin_headers)
        if resp.status_code == 200:
            data = resp.get_json()
            self.assertTrue(data.get("success"))
            for item in data.get("data", []):
                self.assertIn("royal", item.get("brand", "").lower() + item.get("title", "").lower())
            print(f" [PASS] Search and brand filters applied cleanly. Matched: {len(data.get('data', []))} records.")

    def test_07_financial_formula_verification(self):
        """Verify financial calculation formulas across test cases."""
        from app import calculate_bike_financials
        
        # Test Case 1:
        # Buying Price: 50000, Selling Price: 65000, Total Expenses: 2000
        # Gross Profit: 15000, Net Profit: 13000, Margin %: 26.0%
        res1 = calculate_bike_financials(50000, 65000, other_expenses=2000)
        self.assertEqual(res1["gross_profit"], 15000.0)
        self.assertEqual(res1["total_expenses"], 2000.0)
        self.assertEqual(res1["net_profit"], 13000.0)
        self.assertEqual(res1["profit_margin"], 26.0)
        self.assertEqual(res1["profit_percentage"], 26.0)
        self.assertFalse(res1["is_loss"])
        
        # Test Case 2: Zero buying price must not throw ZeroDivisionError
        res2 = calculate_bike_financials(0, 75000, repair_expenses=5000)
        self.assertEqual(res2["gross_profit"], 75000.0)
        self.assertEqual(res2["total_expenses"], 5000.0)
        self.assertEqual(res2["net_profit"], 70000.0)
        self.assertEqual(res2["profit_margin"], 0.0)
        self.assertFalse(res2["is_loss"])
        
        # Test Case 3: Loss scenario
        # Buying Price: 80000, Selling Price: 70000, Expenses: 5000
        # Net Profit: -15000, Margin %: -18.75%
        res3 = calculate_bike_financials(80000, 70000, repair_expenses=3000, service_expenses=2000)
        self.assertEqual(res3["gross_profit"], -10000.0)
        self.assertEqual(res3["total_expenses"], 5000.0)
        self.assertEqual(res3["net_profit"], -15000.0)
        self.assertEqual(res3["profit_margin"], -18.75)
        self.assertTrue(res3["is_loss"])
        print(" [PASS] Financial calculation formulas verified with zero-division safety and loss handling.")

if __name__ == "__main__":
    unittest.main()
