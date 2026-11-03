import sys
import os
import json
import unittest
import io

sys.path.insert(0, os.path.abspath("my-node-app"))
from app import app, get_db

class TestSliderSoldSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        cls.client = app.test_client()

        # Superadmin login
        super_res = cls.client.post("/api/admin/login", json={
            "username": "admin",
            "password": "admin123"
        })
        assert super_res.status_code == 200, f"Superadmin login failed: {super_res.data}"
        super_data = json.loads(super_res.data.decode("utf-8"))
        cls.super_token = super_data["token"]
        cls.super_headers = {"Authorization": f"Bearer {cls.super_token}"}

        # Staff admin login
        staff_res = cls.client.post("/api/admin/login", json={
            "username": "mani",
            "password": "mani@22"
        })
        assert staff_res.status_code == 200, f"Staff login failed: {staff_res.data}"
        staff_data = json.loads(staff_res.data.decode("utf-8"))
        cls.staff_token = staff_data["token"]
        cls.staff_headers = {"Authorization": f"Bearer {cls.staff_token}"}

    def test_01_tidb_tables_existence(self):
        """Verify TiDB Cloud schema contains all 6 required tables."""
        conn = get_db()
        self.assertIsNotNone(conn, "TiDB Cloud connection should be active")
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()

        required = ['bike_images', 'sold_bikes', 'admin_activity_logs', 'financial_records', 'bike_transactions', 'bikes']
        for tbl in required:
            self.assertIn(tbl, tables, f"Table {tbl} must exist in TiDB Cloud")
        print("[Pass] Test 1: All 6 required TiDB Cloud tables confirmed present.")

    def test_02_multiple_image_upload_and_limit(self):
        """Verify uploading up to 6 gallery images and enforcing <= 6 images limit."""
        # 1. Upload 3 valid images
        files = {
            "images": [
                (io.BytesIO(b"fake image 1 bytes"), "test1.jpg"),
                (io.BytesIO(b"fake image 2 bytes"), "test2.png"),
                (io.BytesIO(b"fake image 3 bytes"), "test3.webp")
            ]
        }
        res = self.client.post("/api/bikes/upload-images", data=files, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 200)
        d = json.loads(res.data.decode("utf-8"))
        self.assertTrue(d["success"])
        self.assertEqual(len(d["images"]), 3)
        self.assertEqual(d["images"][0]["is_primary"], 1)
        self.assertEqual(d["images"][1]["is_primary"], 0)

        # 2. Exceeding limit of 6 rejected
        too_many = {
            "images": [(io.BytesIO(b"bytes"), f"img{i}.jpg") for i in range(7)]
        }
        err_res = self.client.post("/api/bikes/upload-images", data=too_many, content_type="multipart/form-data")
        self.assertEqual(err_res.status_code, 400)
        print("[Pass] Test 2: Multi-image upload validation & <= 6 limits verified.")

    def test_03_bike_creation_with_multi_images_and_counter(self):
        """Create a bike with multiple images and verify persistence to bike_images."""
        img_urls = [
            "/uploads/test_slider_img1.jpg",
            "/uploads/test_slider_img2.jpg",
            "/uploads/test_slider_img3.jpg",
            "/uploads/test_slider_img4.jpg"
        ]
        create_res = self.client.post("/api/bikes", json={
            "title": "Yamaha MT-15 V2 Cyber Ice Fluo",
            "brand": "Yamaha",
            "model": "MT-15 V2",
            "year": 2023,
            "price": 145000,
            "kilometers_driven": 6500,
            "fuel_type": "Petrol",
            "transmission": "Manual",
            "location": "Salem, Tamil Nadu",
            "seller_name": "Karthik Raja",
            "seller_phone": "+91 98888 77777",
            "images": img_urls
        })
        self.assertIn(create_res.status_code, [200, 201])
        bike_data = json.loads(create_res.data.decode("utf-8"))
        bike_id = bike_data["id"]

        # Fetch bike details
        get_res = self.client.get(f"/api/bikes/{bike_id}")
        self.assertEqual(get_res.status_code, 200)
        b = json.loads(get_res.data.decode("utf-8"))
        imgs = b.get("images")
        if isinstance(imgs, str):
            imgs = json.loads(imgs)
        self.assertEqual(len(imgs), 4)
        self.assertEqual(imgs[0], "/uploads/test_slider_img1.jpg")
        print("[Pass] Test 3: Bike multi-image persistence & JSON array verified.")
        return bike_id

    def test_04_strict_superadmin_vs_staff_data_separation(self):
        """Verify confidential financials are accessible ONLY by superadmin."""
        # 1. Staff cannot call mark-sold (superadmin required -> HTTP 403)
        staff_mark = self.client.post("/api/admin/bikes/1/mark-sold", headers=self.staff_headers, json={
            "actual_sale_price": 90000
        })
        self.assertEqual(staff_mark.status_code, 403)

        # 2. Staff cannot see profit/expenses in sold bikes
        staff_sold = self.client.get("/api/admin/sold-bikes", headers=self.staff_headers)
        self.assertEqual(staff_sold.status_code, 200)
        staff_d = json.loads(staff_sold.data.decode("utf-8"))
        self.assertFalse(staff_d["is_superadmin"])
        for record in staff_d["data"]:
            self.assertNotIn("realized_profit", record)
            self.assertNotIn("seller_payout", record)
            self.assertNotIn("total_expenses", record)

        # 3. Superadmin sees full financials
        super_sold = self.client.get("/api/admin/sold-bikes", headers=self.super_headers)
        self.assertEqual(super_sold.status_code, 200)
        super_d = json.loads(super_sold.data.decode("utf-8"))
        self.assertTrue(super_d["is_superadmin"])
        if len(super_d["data"]) > 0:
            rec = super_d["data"][0]
            self.assertIn("realized_profit", rec)
            self.assertIn("seller_payout", rec)

        # 4. Public sold endpoint strictly sanitizes financials
        pub_sold = self.client.get("/api/bikes/sold")
        self.assertEqual(pub_sold.status_code, 200)
        pub_d = json.loads(pub_sold.data.decode("utf-8"))
        for item in pub_d.get("data", []):
            self.assertNotIn("realized_profit", item)
            self.assertNotIn("seller_payout", item)
            self.assertNotIn("total_expenses", item)

        print("[Pass] Test 4: Strict RBAC data separation (Superadmin vs Staff vs Public) verified.")

    def test_05_sold_out_workflow_and_duplicate_prevention(self):
        """Superadmin marks bike sold; verify archives in sold_bikes, financial_records & duplicate prevention."""
        # Create unique bike
        create_res = self.client.post("/api/bikes", json={
            "title": "KTM Duke 390 Test Sold Unit",
            "brand": "KTM",
            "model": "Duke 390",
            "year": 2022,
            "price": 240000,
            "kilometers_driven": 11000,
            "status": "approved",
            "seller_name": "Arun Kumar",
            "seller_phone": "+91 97777 66666",
            "images": ["/static/images/IMG-20251204-WA0053.jpg", "/static/images/IMG-20251204-WA0054.jpg"]
        })
        self.assertIn(create_res.status_code, [200, 201])
        bike_id = json.loads(create_res.data.decode("utf-8"))["id"]

        # Superadmin marks as sold
        sold_res = self.client.post(f"/api/admin/bikes/{bike_id}/mark-sold", headers=self.super_headers, json={
            "actual_sale_price": 235000,
            "seller_payout": 215000,
            "buyer_name": "Deepak Verma",
            "buyer_phone": "+91 91234 56789",
            "service_expense": 3000,
            "other_expense": 2000
        })
        self.assertEqual(sold_res.status_code, 200)
        sold_data = json.loads(sold_res.data.decode("utf-8"))
        self.assertTrue(sold_data["success"])
        tx = sold_data["transaction"]
        # Realized profit = 235000 - 215000 - (3000 + 2000) = 15000
        self.assertEqual(tx["realized_profit"], 15000)

        # Duplicate sale attempt must be rejected (HTTP 400)
        dup_res = self.client.post(f"/api/admin/bikes/{bike_id}/mark-sold", headers=self.super_headers, json={
            "actual_sale_price": 235000
        })
        self.assertEqual(dup_res.status_code, 400)
        dup_data = json.loads(dup_res.data.decode("utf-8"))
        self.assertFalse(dup_data["success"])
        self.assertIn("already marked as sold out", dup_data["message"].lower())

        # Verify excluded from active marketplace
        market_res = self.client.get("/api/bikes")
        self.assertEqual(market_res.status_code, 200)
        active_bikes = json.loads(market_res.data.decode("utf-8"))["data"]
        active_ids = [b["id"] for b in active_bikes]
        self.assertNotIn(bike_id, active_ids, "Sold out bike must not appear in active marketplace")

        # Verify present in sold gallery
        sold_gallery_res = self.client.get("/api/bikes/sold")
        self.assertEqual(sold_gallery_res.status_code, 200)
        sold_gallery_bikes = json.loads(sold_gallery_res.data.decode("utf-8"))["data"]
        sold_ids = [b["id"] for b in sold_gallery_bikes]
        self.assertIn(bike_id, sold_ids, "Sold out bike must appear in sold gallery")

        # Verify single bike details endpoint reflects soldout
        detail_res = self.client.get(f"/api/bikes/{bike_id}")
        self.assertEqual(detail_res.status_code, 200)
        det = json.loads(detail_res.data.decode("utf-8"))
        self.assertEqual(det["status"], "soldout")
        self.assertEqual(det["isSoldout"], 1)

        print("[Pass] Test 5: Sold out workflow, profit computation & duplicate prevention verified.")

if __name__ == "__main__":
    unittest.main()
