import unittest
import json
import os
import sys

# Ensure my-node-app is in path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_DIR = os.path.join(BASE_DIR, "my-node-app")
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from app import app, JWT_SECRET, get_db
import jwt
import datetime

class PriceLimitAndFeaturedRemovalTests(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

        # Generate mock JWT tokens
        now = datetime.datetime.now(datetime.timezone.utc)
        self.user_token = jwt.encode({
            'user_id': 9999,
            'email': 'rider@example.com',
            'role': 'user',
            'exp': now + datetime.timedelta(hours=2)
        }, JWT_SECRET, algorithm='HS256')

        self.admin_token = jwt.encode({
            'admin_id': 1,
            'username': 'admin_tester',
            'role': 'admin',
            'exp': now + datetime.timedelta(hours=2)
        }, JWT_SECRET, algorithm='HS256')

        self.superadmin_token = jwt.encode({
            'admin_id': 2,
            'username': 'super_tester',
            'role': 'superadmin',
            'exp': now + datetime.timedelta(hours=2)
        }, JWT_SECRET, algorithm='HS256')

    # Test 10 & 11: Homepage verifies absence of Motorcycle Spotlight and presence of normal inventory & sold page
    def test_10_homepage_no_featured_spotlight(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertNotIn("Motorcycle Spotlight", html)
        self.assertNotIn("showcase-carousel-wrap", html)
        self.assertNotIn("carousel-track", html)
        self.assertIn("Explore Available Motorcycles", html)
        self.assertIn("marketplace-bikes-grid", html)

    def test_11_sold_gallery_accessible(self):
        response = self.app.get('/SoldOutPage.html')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Recently Delivered Motorcycles", html)

    # Test 1: User submits bike at ₹0 – accepted
    def test_01_user_submits_bike_at_0(self):
        payload = {
            "title": "Yamaha Test 0",
            "brand": "Yamaha",
            "model": "R15",
            "year": 2022,
            "price": 0,
            "kilometers_driven": 5000,
            "registration_number": "TN-01-AB-0000"
        }
        res = self.app.post('/api/bikes', data=json.dumps(payload), content_type='application/json')
        self.assertIn(res.status_code, [200, 201])
        data = res.get_json()
        self.assertTrue(data.get("success"))

    # Test 2: User submits bike at ₹5,000 – accepted
    def test_02_user_submits_bike_at_5000(self):
        payload = {
            "title": "Hero Splendor 5k",
            "brand": "Hero",
            "model": "Splendor",
            "year": 2018,
            "price": 5000,
            "kilometers_driven": 25000,
            "registration_number": "TN-01-AB-5000"
        }
        res = self.app.post('/api/bikes', data=json.dumps(payload), content_type='application/json')
        self.assertIn(res.status_code, [200, 201])
        data = res.get_json()
        self.assertTrue(data.get("success"))

    # Test 3: User submits bike at ₹10,00,000 (10 Lakhs) – accepted
    def test_03_user_submits_bike_at_10lakh(self):
        payload = {
            "title": "Kawasaki Ninja 10L",
            "brand": "Kawasaki",
            "model": "ZX-10R",
            "year": 2023,
            "price": 1000000,
            "kilometers_driven": 2000,
            "registration_number": "TN-01-AB-1000"
        }
        res = self.app.post('/api/bikes', data=json.dumps(payload), content_type='application/json')
        self.assertIn(res.status_code, [200, 201])
        data = res.get_json()
        self.assertTrue(data.get("success"))

    # Test 4: User submits bike at ₹10,00,001 – rejected
    def test_04_user_submits_bike_above_10lakh_rejected(self):
        payload = {
            "title": "Ducati Panigale Expensive",
            "brand": "Ducati",
            "model": "V4",
            "year": 2024,
            "price": 1000001,
            "kilometers_driven": 1000,
            "registration_number": "TN-01-AB-9999"
        }
        res = self.app.post('/api/bikes', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data.get("success"))
        self.assertEqual(data.get("message"), "Bike price must be between ₹0 and ₹10,00,000.")

    # Test 5: User submits negative price – rejected
    def test_05_user_submits_negative_price_rejected(self):
        payload = {
            "title": "Negative Price Bike",
            "brand": "Honda",
            "model": "Activa",
            "year": 2021,
            "price": -500,
            "kilometers_driven": 15000,
            "registration_number": "TN-01-AB-1111"
        }
        res = self.app.post('/api/bikes', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data.get("success"))
        self.assertEqual(data.get("message"), "Bike price must be between ₹0 and ₹10,00,000.")

    # Test 6: Admin submits bike at ₹10,00,000 – accepted
    def test_06_admin_submits_bike_at_10lakh(self):
        payload = {
            "title": "Admin BMW S1000RR",
            "brand": "BMW",
            "model": "S1000RR",
            "year": 2023,
            "price": 1000000,
            "status": "approved",
            "kilometers_driven": 1200,
            "registration_number": "TN-01-AB-1200"
        }
        headers = {'Authorization': f'Bearer {self.superadmin_token}'}
        res = self.app.post('/api/bikes', data=json.dumps(payload), content_type='application/json', headers=headers)
        self.assertIn(res.status_code, [200, 201])
        data = res.get_json()
        self.assertTrue(data.get("success"))

    # Test 7: Admin submits bike above ₹10,00,000 – rejected
    def test_07_admin_submits_bike_above_10lakh_rejected(self):
        payload = {
            "title": "Admin Overpriced Bike",
            "brand": "BMW",
            "model": "M1000RR",
            "year": 2024,
            "price": 1500000,
            "status": "approved",
            "kilometers_driven": 500,
            "registration_number": "TN-01-AB-1500"
        }
        headers = {'Authorization': f'Bearer {self.superadmin_token}'}
        res = self.app.post('/api/bikes', data=json.dumps(payload), content_type='application/json', headers=headers)
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data.get("success"))
        self.assertEqual(data.get("message"), "Bike price must be between ₹0 and ₹10,00,000.")

    # Test 8: Admin edits price within range – accepted
    def test_08_admin_edits_price_within_range_accepted(self):
        headers = {'Authorization': f'Bearer {self.superadmin_token}'}
        # First ensure a bike exists (e.g., bike 1)
        res = self.app.put('/api/admin/bikes/1/price',
                           data=json.dumps({"price": 350000}),
                           content_type='application/json',
                           headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))

        # Also test via admin update endpoint
        update_payload = {
            "price": 450000,
            "requested_price": 420000
        }
        res_put = self.app.put('/api/admin/bikes/1',
                               data=json.dumps(update_payload),
                               content_type='application/json',
                               headers=headers)
        self.assertEqual(res_put.status_code, 200)

    # Test 9: Direct API request with invalid price – rejected
    def test_09_direct_api_request_invalid_price_rejected(self):
        headers = {'Authorization': f'Bearer {self.superadmin_token}'}

        # 9a: Text / non-numeric price
        res = self.app.post('/api/bikes',
                            data=json.dumps({"title": "Bad Price", "price": "ten lakhs"}),
                            content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.get_json().get("message"), "Bike price must be between ₹0 and ₹10,00,000.")

        # 9b: Null / empty price
        res = self.app.post('/api/bikes',
                            data=json.dumps({"title": "Empty Price", "price": ""}),
                            content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.get_json().get("message"), "Bike price must be between ₹0 and ₹10,00,000.")

        # 9c: Admin PUT price above 10 Lakhs
        res = self.app.put('/api/admin/bikes/1/price',
                           data=json.dumps({"price": 1000001}),
                           content_type='application/json',
                           headers=headers)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.get_json().get("message"), "Bike price must be between ₹0 and ₹10,00,000.")

        # 9d: Admin PUT negative price
        res = self.app.put('/api/admin/bikes/1/price',
                           data=json.dumps({"price": -100}),
                           content_type='application/json',
                           headers=headers)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.get_json().get("message"), "Bike price must be between ₹0 and ₹10,00,000.")

        # 9e: Admin update bike with price > 10 Lakhs
        res = self.app.put('/api/admin/bikes/1',
                           data=json.dumps({"price": 1200000}),
                           content_type='application/json',
                           headers=headers)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.get_json().get("message"), "Bike price must be between ₹0 and ₹10,00,000.")

if __name__ == '__main__':
    unittest.main()
