"""
Unit and Integration Tests for SMR Motors Homepage Filter Logic
Verifies expected behavior:
- Apply filters only when explicitly selected/modified.
- No default brand, model, price, year, or category filter applied.
- All approved bikes shown by default (including high-value bikes up to 10 Lakhs).
- Explicit filters correctly filter matching bikes.
- Resetting/clearing filters returns all available bikes.
- Preserves search, sorting, and pagination.
"""

import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_DIR = os.path.join(BASE_DIR, "my-node-app")
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import app, get_db


class HomepageFilterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        cls.client = app.test_client()

    def test_01_default_homepage_shows_all_approved_bikes(self):
        """When no filters are provided, all available approved bikes are returned."""
        res = self.client.get("/api/bikes?page=1&limit=50&sort=newest")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        bikes = data.get("bikes") or data.get("data") or []
        self.assertGreater(len(bikes), 0, "Default inventory should not be empty")

        # Ensure no default brand filter is applied: check if multiple brands are present
        brands = set(b.get("brand") for b in bikes if b.get("brand"))
        self.assertGreaterEqual(len(brands), 2, f"Expected multiple brands, got {brands}")

        # Ensure no default price cap (e.g. 5L or 6L) is applied: check high-value bike
        has_high_value = any(float(b.get("price", 0)) > 600000 for b in bikes)
        self.assertTrue(has_high_value, "High value bikes (> 6 Lakhs) must not be filtered out by default")

        # Ensure no sold bikes appear in active inventory
        for b in bikes:
            self.assertNotEqual(b.get("isSoldout"), 1, f"Sold bike #{b.get('id')} found in active inventory")
            self.assertNotIn(str(b.get("status", "")).lower(), ("sold", "soldout"))
            self.assertIn(str(b.get("status", "")).lower(), ("approved", "published"))

    def test_02_explicit_brand_filter(self):
        """When user explicitly selects a brand, only that brand is returned."""
        res = self.client.get("/api/bikes?brand=BMW")
        self.assertEqual(res.status_code, 200)
        bikes = res.get_json().get("bikes") or []
        self.assertGreater(len(bikes), 0, "Expected BMW bikes to be found")
        for b in bikes:
            self.assertEqual(b.get("brand"), "BMW")

        # Test another brand
        res_re = self.client.get("/api/bikes?brand=Royal%20Enfield")
        self.assertEqual(res_re.status_code, 200)
        re_bikes = res_re.get_json().get("bikes") or []
        self.assertGreater(len(re_bikes), 0)
        for b in re_bikes:
            self.assertEqual(b.get("brand"), "Royal Enfield")

    def test_03_explicit_price_filter(self):
        """When user explicitly adjusts the max budget slider, only bikes <= max_price are returned."""
        res = self.client.get("/api/bikes?max_price=200000")
        self.assertEqual(res.status_code, 200)
        bikes = res.get_json().get("bikes") or []
        self.assertGreater(len(bikes), 0)
        for b in bikes:
            self.assertLessEqual(float(b.get("price", 0)), 200000.0)

    def test_04_explicit_search_keyword(self):
        """When user types in search box, only keyword matches are returned."""
        res = self.client.get("/api/bikes?search=Hunter")
        self.assertEqual(res.status_code, 200)
        bikes = res.get_json().get("bikes") or []
        self.assertGreater(len(bikes), 0)
        for b in bikes:
            text = f"{b.get('title')} {b.get('brand')} {b.get('model')} {b.get('description')}".lower()
            self.assertIn("hunter", text)

    def test_05_explicit_sorting(self):
        """Sorting options work correctly."""
        # Price Low to High
        res_asc = self.client.get("/api/bikes?sort=price_asc&limit=50")
        self.assertEqual(res_asc.status_code, 200)
        bikes_asc = res_asc.get_json().get("bikes") or []
        prices_asc = [float(b.get("price", 0)) for b in bikes_asc]
        self.assertEqual(prices_asc, sorted(prices_asc))

        # Price High to Low
        res_desc = self.client.get("/api/bikes?sort=price_desc&limit=50")
        self.assertEqual(res_desc.status_code, 200)
        bikes_desc = res_desc.get_json().get("bikes") or []
        prices_desc = [float(b.get("price", 0)) for b in bikes_desc]
        self.assertEqual(prices_desc, sorted(prices_desc, reverse=True))

    def test_06_reset_filters_restores_all_bikes(self):
        """When filters are reset/empty, all approved bikes are displayed again."""
        # Query with filters
        res_filtered = self.client.get("/api/bikes?brand=BMW&max_price=100000")
        data_filtered = res_filtered.get_json().get("bikes") or []
        self.assertEqual(len(data_filtered), 0, "No BMW should exist under 100k")

        # Query after reset (empty filter parameters)
        res_reset = self.client.get("/api/bikes?page=1&limit=50&sort=newest")
        data_reset = res_reset.get_json().get("bikes") or []
        self.assertGreater(len(data_reset), 0)

        # All brands and price tiers present
        bmw_present = any(b.get("brand") == "BMW" for b in data_reset)
        re_present = any(b.get("brand") == "Royal Enfield" for b in data_reset)
        self.assertTrue(bmw_present, "BMW should be visible after reset")
        self.assertTrue(re_present, "Royal Enfield should be visible after reset")

    def test_07_server_side_pagination(self):
        """Pagination returns accurate chunk sizes and total count."""
        res_page1 = self.client.get("/api/bikes?page=1&limit=6&sort=newest")
        self.assertEqual(res_page1.status_code, 200)
        data1 = res_page1.get_json()
        bikes1 = data1.get("bikes") or []
        self.assertLessEqual(len(bikes1), 6)
        pagination1 = data1.get("pagination")
        self.assertIsNotNone(pagination1)
        self.assertEqual(pagination1.get("page"), 1)
        self.assertEqual(pagination1.get("limit"), 6)

        if pagination1.get("totalPages", 1) > 1:
            res_page2 = self.client.get("/api/bikes?page=2&limit=6&sort=newest")
            self.assertEqual(res_page2.status_code, 200)
            data2 = res_page2.get_json()
            bikes2 = data2.get("bikes") or []
            # Ensure items on page 2 are different from page 1
            ids_page1 = set(b["id"] for b in bikes1)
            ids_page2 = set(b["id"] for b in bikes2)
            self.assertEqual(len(ids_page1.intersection(ids_page2)), 0)


if __name__ == "__main__":
    unittest.main()
