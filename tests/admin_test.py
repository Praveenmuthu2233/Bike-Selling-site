import sys
import os
import json
import unittest

sys.path.insert(0, os.path.abspath("my-node-app"))
import app as flask_module
from app import app, get_db

class TestAdminPlatform(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        cls.client = app.test_client()

        # Login as superadmin to get token
        login_res = cls.client.post("/api/admin/login", json={
            "username": "admin",
            "password": "admin123"
        })
        assert login_res.status_code == 200, f"Superadmin login failed: {login_res.get_data(as_text=True)}"
        data = json.loads(login_res.get_data(as_text=True))
        cls.super_token = data["token"]
        cls.super_headers = {"Authorization": f"Bearer {cls.super_token}"}

        # Login as staff admin (limited)
        staff_res = cls.client.post("/api/admin/login", json={
            "username": "mani",
            "password": "mani@22"
        })
        assert staff_res.status_code == 200, f"Staff login failed: {staff_res.get_data(as_text=True)}"
        staff_data = json.loads(staff_res.get_data(as_text=True))
        cls.staff_token = staff_data["token"]
        cls.staff_headers = {"Authorization": f"Bearer {cls.staff_token}"}

    def test_01_config_diagnostics(self):
        res = self.client.get("/api/config")
        self.assertEqual(res.status_code, 200)
        d = json.loads(res.get_data(as_text=True))
        self.assertTrue(d["success"])
        self.assertIn("https://bike-selling-site-lco8.onrender.com", d["authorizedOrigins"])
        self.assertIn("https://bike-selling-site-lco8.onrender.com/api/auth/google/callback", d["authorizedRedirectUris"])
        print("[Pass] Test 1: /api/config returned authorized origins and diagnostics.")

    def test_02_staff_crud_and_rbac(self):
        # 1. Staff admin cannot access staff management (HTTP 403)
        forbidden_res = self.client.get("/api/admin/staff", headers=self.staff_headers)
        self.assertEqual(forbidden_res.status_code, 403)

        # 2. Superadmin lists staff
        res = self.client.get("/api/admin/staff", headers=self.super_headers)
        self.assertEqual(res.status_code, 200)
        staff_list = json.loads(res.get_data(as_text=True))["staff"]
        self.assertTrue(len(staff_list) >= 4)

        # 3. Create new staff member
        test_uname = "teststaff99"
        create_res = self.client.post("/api/admin/staff", headers=self.super_headers, json={
            "username": test_uname,
            "full_name": "Test Staff Member",
            "email": "teststaff99@smrmotors.com",
            "phone": "+91 99999 88888",
            "password": "password123",
            "role": "admin"
        })
        self.assertEqual(create_res.status_code, 201)
        new_id = json.loads(create_res.get_data(as_text=True))["id"]

        # 4. Edit staff member
        edit_res = self.client.put(f"/api/admin/staff/{new_id}", headers=self.super_headers, json={
            "full_name": "Updated Staff Name",
            "phone": "+91 99999 77777"
        })
        self.assertEqual(edit_res.status_code, 200)

        # 5. Toggle status (Deactivate)
        deact_res = self.client.put(f"/api/admin/staff/{new_id}/status", headers=self.super_headers, json={"is_active": 0})
        self.assertEqual(deact_res.status_code, 200)

        # 6. Deactivated staff cannot login (HTTP 403)
        deact_login = self.client.post("/api/admin/login", json={
            "username": test_uname,
            "password": "password123"
        })
        self.assertEqual(deact_login.status_code, 403)

        # 7. Delete staff member
        del_res = self.client.delete(f"/api/admin/staff/{new_id}", headers=self.super_headers)
        self.assertEqual(del_res.status_code, 200)

        # 8. Check staff activity logs
        act_res = self.client.get("/api/admin/staff/activity", headers=self.super_headers)
        self.assertEqual(act_res.status_code, 200)
        logs = json.loads(act_res.get_data(as_text=True))["data"]
        self.assertTrue(len(logs) > 0)
        print("[Pass] Test 2: Staff CRUD, RBAC, Status Toggle, and Activity Logs verified.")

    def test_03_bike_management_and_subtabs(self):
        # 1. Fetch all bikes
        res_all = self.client.get("/api/admin/bikes?tab=all", headers=self.super_headers)
        self.assertEqual(res_all.status_code, 200)
        all_bikes = json.loads(res_all.get_data(as_text=True))["data"]
        self.assertTrue(len(all_bikes) > 0)

        # Verify all required fields
        sample = all_bikes[0]
        for field in ["id", "title", "brand", "model", "year", "kilometers_driven", "registration_number", "fuel_type", "owner_name", "seller_phone", "requested_price", "approved_price", "status"]:
            self.assertIn(field, sample, f"Missing required field {field} in motorcycle model")

        # 2. Fetch pending bikes
        res_pending = self.client.get("/api/admin/bikes?tab=pending", headers=self.super_headers)
        self.assertEqual(res_pending.status_code, 200)

        # 3. Edit bike details
        target_id = sample["id"]
        edit_res = self.client.put(f"/api/admin/bikes/{target_id}", headers=self.super_headers, json={
            "description": "Thoroughly tested and certified pre-owned motorcycle."
        })
        self.assertEqual(edit_res.status_code, 200)

        # 4. Sold bikes endpoint
        res_sold = self.client.get("/api/admin/sold-bikes", headers=self.super_headers)
        self.assertEqual(res_sold.status_code, 200)
        sold_data = json.loads(res_sold.get_data(as_text=True))
        self.assertTrue(sold_data["is_superadmin"])

        # Staff gets sanitized sold bikes
        res_sold_staff = self.client.get("/api/admin/sold-bikes", headers=self.staff_headers)
        self.assertEqual(res_sold_staff.status_code, 200)
        sold_staff_data = json.loads(res_sold_staff.get_data(as_text=True))
        self.assertFalse(sold_staff_data["is_superadmin"])
        if len(sold_staff_data["data"]) > 0:
            self.assertNotIn("realized_profit", sold_staff_data["data"][0])

        print("[Pass] Test 3: Bike Management sub-tabs, full fields, and sold bikes verified.")

    def test_04_enquiry_management(self):
        # 1. Create enquiry
        post_res = self.client.post("/api/enquiries", json={
            "bike_id": 1,
            "bike_title": "Royal Enfield Hunter 350 Dapper Ash",
            "name": "Karthik Raja",
            "email": "karthik.raja@example.com",
            "phone": "+91 94444 33333",
            "message": "Interested in inspecting RC book and test ride tomorrow."
        })
        self.assertEqual(post_res.status_code, 201)
        enq_id = json.loads(post_res.get_data(as_text=True))["id"]

        # 2. List enquiries
        list_res = self.client.get("/api/admin/enquiries?status=all", headers=self.super_headers)
        self.assertEqual(list_res.status_code, 200)
        enqs = json.loads(list_res.get_data(as_text=True))["data"]
        self.assertTrue(len(enqs) > 0)

        # Verify required fields
        sample_enq = enqs[0]
        for field in ["id", "customer_name", "customer_email", "customer_phone", "bike_id", "bike_title", "message", "status", "created_at"]:
            self.assertIn(field, sample_enq, f"Missing field {field} in enquiry model")

        # 3. Update enquiry status
        stat_res = self.client.post(f"/api/admin/enquiries/{enq_id}/status", headers=self.super_headers, json={"status": "accepted"})
        self.assertEqual(stat_res.status_code, 200)

        # 4. Reply to enquiry (Email & enquiry_replies table)
        rep_res = self.client.post(f"/api/admin/enquiries/{enq_id}/reply", headers=self.super_headers, json={
            "reply_message": "Hello Karthik, your test ride is confirmed for 11:00 AM at our showroom."
        })
        self.assertEqual(rep_res.status_code, 200)

        # 5. Fetch enquiry replies
        history_res = self.client.get(f"/api/admin/enquiries/{enq_id}/replies", headers=self.super_headers)
        self.assertEqual(history_res.status_code, 200)
        replies = json.loads(history_res.get_data(as_text=True))["replies"]
        self.assertTrue(len(replies) > 0)
        print("[Pass] Test 4: Enquiry management, status updates, email replies & reply history verified.")

    def test_05_user_management(self):
        # 1. List users
        res = self.client.get("/api/admin/users?status=all", headers=self.super_headers)
        self.assertEqual(res.status_code, 200)
        users = json.loads(res.get_data(as_text=True))["data"]
        self.assertTrue(len(users) > 0)

        # Verify required fields
        u = users[0]
        for field in ["id", "name", "email", "profile_image", "role", "is_active", "created_at"]:
            self.assertIn(field, u, f"Missing field {field} in user model")

        # 2. Get user profile with listings & enquiries
        user_id = u["id"]
        prof_res = self.client.get(f"/api/admin/users/{user_id}", headers=self.super_headers)
        self.assertEqual(prof_res.status_code, 200)
        prof_data = json.loads(prof_res.get_data(as_text=True))
        self.assertIn("user", prof_data)
        self.assertIn("listings", prof_data)
        self.assertIn("enquiries", prof_data)

        # 3. Toggle user status
        toggle_res = self.client.put(f"/api/admin/users/{user_id}/status", headers=self.super_headers, json={"is_active": 0})
        self.assertEqual(toggle_res.status_code, 200)
        toggle_back = self.client.put(f"/api/admin/users/{user_id}/status", headers=self.super_headers, json={"is_active": 1})
        self.assertEqual(toggle_back.status_code, 200)
        print("[Pass] Test 5: User Management listing, profile modal data, and status toggling verified.")

if __name__ == "__main__":
    unittest.main()
