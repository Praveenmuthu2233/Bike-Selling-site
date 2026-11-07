import sys
import os
import io
import unittest
import datetime
import json
import jwt
from unittest.mock import MagicMock, patch

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'my-node-app'))

from app import app, JWT_SECRET, calculate_bike_financials

class TestBuyingPriceAndDocumentDownload(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        app.config["TESTING"] = True

        # Valid Admin Token
        admin_payload = {
            "id": 2,
            "username": "staff_admin",
            "role": "admin",
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)
        }
        self.admin_token = jwt.encode(admin_payload, JWT_SECRET, algorithm="HS256")
        self.admin_headers = {"Authorization": f"Bearer {self.admin_token}"}

        # Valid Superadmin Token
        super_payload = {
            "id": 1,
            "username": "owner_admin",
            "role": "superadmin",
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)
        }
        self.superadmin_token = jwt.encode(super_payload, JWT_SECRET, algorithm="HS256")
        self.superadmin_headers = {"Authorization": f"Bearer {self.superadmin_token}"}

        # Expired Token
        expired_payload = {
            "id": 1,
            "username": "expired_admin",
            "role": "admin",
            "exp": datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)
        }
        self.expired_token = jwt.encode(expired_payload, JWT_SECRET, algorithm="HS256")

        # Normal User Token
        user_payload = {
            "id": 99,
            "username": "normal_user",
            "role": "user",
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)
        }
        self.user_token = jwt.encode(user_payload, JWT_SECRET, algorithm="HS256")

    # =========================================================================
    # 1. AUTHENTICATION & TOKEN EXTRACTION (HEADER, QUERY, COOKIE)
    # =========================================================================
    def test_missing_auth_returns_401(self):
        resp = self.client.get("/api/admin/sold-bikes/1001")
        self.assertEqual(resp.status_code, 401)
        data = resp.get_json()
        self.assertFalse(data["success"])
        self.assertIn("Missing admin authorization header", data["message"])

    def test_expired_token_returns_401(self):
        resp = self.client.get("/api/admin/sold-bikes/1001", headers={"Authorization": f"Bearer {self.expired_token}"})
        self.assertEqual(resp.status_code, 401)
        data = resp.get_json()
        self.assertIn("expired", data["message"].lower())

    def test_auth_via_query_parameter(self):
        # Even without Authorization header, passing ?token=<valid_token> should authenticate
        with patch("app.get_db") as mock_get_db:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_get_db.return_value = mock_conn

            mock_cursor.fetchone.return_value = {
                "id": 1001,
                "title": "Yamaha R15 V4",
                "brand": "Yamaha",
                "model": "R15 V4",
                "price": 100000,
                "buying_price": 100000,
                "status": "sold",
                "isSoldout": 1
            }
            mock_cursor.fetchall.return_value = []

            resp = self.client.get(f"/api/admin/sold-bikes/1001?token={self.admin_token}")
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertTrue(data["success"])

    # =========================================================================
    # 2. DOCUMENT DOWNLOAD ENDPOINTS (BLOB, ATTACHMENT, RBAC)
    # =========================================================================
    def test_document_download_blob_with_bearer_header(self):
        dummy_pdf_content = b"%PDF-1.4 mock binary content of registration certificate"
        with patch("app.get_db") as mock_get_db:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_get_db.return_value = mock_conn

            mock_cursor.fetchone.return_value = {
                "id": 42,
                "bike_id": 1001,
                "user_id": 99,
                "file_name": "rc_book_1001.pdf",
                "mime_type": "application/pdf",
                "file_data": dummy_pdf_content
            }

            resp = self.client.get("/api/documents/42/download", headers=self.admin_headers)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.data, dummy_pdf_content)
            self.assertEqual(resp.headers.get("Content-Type"), "application/pdf")
            self.assertIn("attachment", resp.headers.get("Content-Disposition", ""))
            self.assertIn("rc_book_1001.pdf", resp.headers.get("Content-Disposition", ""))

    def test_document_download_with_query_token(self):
        dummy_content = b"Image binary jpeg bytes"
        with patch("app.get_db") as mock_get_db:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_get_db.return_value = mock_conn

            mock_cursor.fetchone.return_value = {
                "id": 55,
                "bike_id": 1001,
                "user_id": 88,
                "file_name": "insurance.jpg",
                "mime_type": "image/jpeg",
                "file_data": dummy_content
            }

            resp = self.client.get(f"/api/documents/55/download?token={self.admin_token}")
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.data, dummy_content)
            self.assertEqual(resp.headers.get("Content-Type"), "image/jpeg")

    def test_document_download_unauthorized_user(self):
        with patch("app.get_db") as mock_get_db:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_get_db.return_value = mock_conn

            # Belongs to user_id 77, caller is user_id 99
            mock_cursor.fetchone.return_value = {
                "id": 60,
                "user_id": 77,
                "file_name": "secret.pdf",
                "file_data": b"dummy"
            }

            resp = self.client.get(f"/api/documents/60/download?token={self.user_token}")
            self.assertEqual(resp.status_code, 403)
            data = resp.get_json()
            self.assertFalse(data["success"])

    def test_sale_document_download_rbac(self):
        dummy_proof = b"Customer Aadhaar / Driving License proof document"
        with patch("app.get_db") as mock_get_db:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_get_db.return_value = mock_conn

            mock_cursor.fetchone.return_value = {
                "id": 10,
                "bike_id": 1001,
                "document_type": "Identity Proof",
                "file_name": "buyer_aadhaar.pdf",
                "mime_type": "application/pdf",
                "file_data": dummy_proof
            }

            # Superadmin download succeeds with 200
            resp_super = self.client.get("/api/admin/sale-documents/10/download", headers=self.superadmin_headers)
            self.assertEqual(resp_super.status_code, 200)
            self.assertEqual(resp_super.data, dummy_proof)

            # Staff Admin receives 403 Forbidden on confidential buyer sale documents
            resp_admin = self.client.get("/api/admin/sale-documents/10/download", headers=self.admin_headers)
            self.assertEqual(resp_admin.status_code, 403)

            # Both Staff Admin and Superadmin can download customer bike ownership documents
            mock_cursor.fetchone.return_value = {
                "id": 20,
                "bike_id": 1001,
                "user_id": 99,
                "file_name": "rc_book.pdf",
                "mime_type": "application/pdf",
                "file_data": b"RC Book binary"
            }
            resp_bike_admin = self.client.get("/api/documents/20/download", headers=self.admin_headers)
            self.assertEqual(resp_bike_admin.status_code, 200)
            resp_bike_super = self.client.get("/api/documents/20/download", headers=self.superadmin_headers)
            self.assertEqual(resp_bike_super.status_code, 200)

    # =========================================================================
    # 3. BUYING PRICE RETRIEVAL & FINANCIAL RECALCULATIONS
    # =========================================================================
    def test_sold_bike_detail_retrieves_buying_price_from_bikes_table(self):
        with patch("app.get_db") as mock_get_db:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_get_db.return_value = mock_conn

            bike_row = {
                "id": 660001,
                "title": "Royal Enfield Classic 350",
                "brand": "Royal Enfield",
                "model": "Classic 350",
                "price": 100000,
                "buying_price": 100000.0,
                "status": "sold",
                "isSoldout": 1
            }
            sold_row = {
                "id": 1,
                "bike_id": 660001,
                "actual_sale_price": 100000.0,
                "buying_price": 100000.0,
                "total_expenses": 0.0,
                "seller_payout": 100000.0
            }

            mock_cursor.fetchone.side_effect = [
                bike_row, # bikes
                None,     # buyer_details
                None,     # sale_documents
                sold_row, # sold_bikes
                None,     # bike_transactions
                None      # financial_records
            ]
            mock_cursor.fetchall.return_value = []

            resp = self.client.get("/api/admin/sold-bikes/660001", headers=self.superadmin_headers)
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            fin = data["data"]["financials"]

            # Expected:
            # Buying Price: ₹100,000 (NOT ₹0)
            # Final Selling Price: ₹100,000
            # Total Expenses: ₹0
            # Gross Profit: ₹0 (100,000 - 100,000 = 0, NOT 100,000!)
            # Net Profit: ₹0 (100,000 - 100,000 - 0 = 0, NOT 100,000!)
            # Profit %: 0%
            self.assertEqual(fin["buying_price"], 100000.0)
            self.assertEqual(fin["formatted_buying_price"], "₹100,000")
            self.assertEqual(fin["selling_price"], 100000.0)
            self.assertEqual(fin["formatted_selling_price"], "₹100,000")
            self.assertEqual(fin["gross_profit"], 0.0)
            self.assertEqual(fin["net_profit"], 0.0)
            self.assertEqual(fin["profit_percentage"], 0.0)

    def test_sold_bike_detail_fallback_to_bike_transactions_seller_payout(self):
        """When bikes.buying_price and sold_bikes are NULL/0, fallback to bike_transactions."""
        with patch("app.get_db") as mock_get_db:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_get_db.return_value = mock_conn

            bike_row = {
                "id": 660002,
                "title": "KTM Duke 200",
                "price": 120000,
                "buying_price": 0.0, # zero in bikes
                "status": "sold",
                "isSoldout": 1
            }
            trans_row = {
                "id": 5,
                "bike_id": 660002,
                "seller_payout": 100000.0, # actual buying price stored in transactions
                "actual_sale_price": 120000.0,
                "total_expenses": 5000.0
            }

            mock_cursor.fetchone.side_effect = [
                bike_row,  # bikes
                None,      # buyer_details
                None,      # sale_documents
                None,      # sold_bikes
                trans_row, # bike_transactions
                None       # financial_records
            ]
            mock_cursor.fetchall.return_value = []

            resp = self.client.get("/api/admin/sold-bikes/660002", headers=self.superadmin_headers)
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            fin = data["data"]["financials"]

            # Resolved BP should be 100000.0
            self.assertEqual(fin["buying_price"], 100000.0)
            self.assertEqual(fin["gross_profit"], 20000.0) # 120,000 - 100,000 = 20,000
            self.assertEqual(fin["net_profit"], 15000.0)   # 120,000 - 100,000 - 5,000 = 15,000
            self.assertEqual(fin["profit_percentage"], 15.0)

    def test_sold_bike_detail_fallback_to_accepted_seller_payout(self):
        """When buying_price is not set in any table, fallback to bikes.accepted_seller_payout."""
        with patch("app.get_db") as mock_get_db:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_get_db.return_value = mock_conn

            bike_row = {
                "id": 660003,
                "title": "TVS Apache RTR 160",
                "price": 95000,
                "buying_price": 0.0,
                "accepted_seller_payout": 80000.0, # agreed customer payout
                "status": "sold",
                "isSoldout": 1
            }

            mock_cursor.fetchone.side_effect = [
                bike_row, # bikes
                None,     # buyer_details
                None,     # sale_documents
                None,     # sold_bikes
                None,     # bike_transactions
                None      # financial_records
            ]
            mock_cursor.fetchall.return_value = []

            resp = self.client.get("/api/admin/sold-bikes/660003", headers=self.superadmin_headers)
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            fin = data["data"]["financials"]

            self.assertEqual(fin["buying_price"], 80000.0)
            self.assertEqual(fin["formatted_buying_price"], "₹80,000")
            self.assertEqual(fin["gross_profit"], 15000.0) # 95,000 - 80,000

    # =========================================================================
    # 4. MARK AS SOLD PRESERVES ORIGINAL BUYING PRICE (NO OVERWRITE WITH 0)
    # =========================================================================
    def test_mark_sold_preserves_buying_price_when_input_is_zero(self):
        with patch("app.get_db") as mock_get_db:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_get_db.return_value = mock_conn

            # Bike originally acquired for 100,000; second fetchone is round-trip verification
            initial_bike = {
                "id": 770001,
                "title": "Honda CB Shine",
                "brand": "Honda",
                "model": "CB Shine",
                "price": 100000,
                "buying_price": 100000.0,
                "accepted_seller_payout": 100000.0,
                "status": "approved",
                "listing_status": "approved",
                "isSoldout": 0
            }
            verified_bike = {
                "id": 770001,
                "status": "sold",
                "listing_status": "sold",
                "isSoldout": 1,
                "sold_at": "2026-11-07",
                "sold_by": "staff_admin"
            }
            mock_cursor.fetchone.side_effect = [
                initial_bike,   # initial lookup
                verified_bike   # round-trip verification
            ]

            sale_payload = {
                "customer_name": "Suresh Kumar",
                "customer_phone": "9876543210",
                "customer_city": "Salem",
                "actual_sale_price": "100000",
                "buying_price": "0", # Admin input is 0 or omitted
                "sale_date": "2026-11-07"
            }

            # Staff admin marks as sold
            resp = self.client.post("/api/admin/bikes/770001/sold", data=sale_payload, headers=self.admin_headers)
            self.assertEqual(resp.status_code, 200)

            # Check executed SQL queries
            # Verify that buying_price written to bikes, sold_bikes, and bike_transactions was 100,000, NOT 0.0
            executed_sql = [call[0][0] for call in mock_cursor.execute.call_args_list]
            executed_args = [call[0][1] for call in mock_cursor.execute.call_args_list if len(call[0]) > 1]

            # Find the UPDATE bikes query
            found_update = False
            for call in mock_cursor.execute.call_args_list:
                sql = call[0][0]
                args = call[0][1] if len(call[0]) > 1 else ()
                if "UPDATE bikes SET" in sql:
                    # buying_price is the 4th parameter (index 3)
                    self.assertEqual(args[3], 100000.0, f"buying_price in UPDATE bikes must be preserved at 100,000! Got {args[3]}")
                    found_update = True
                    break
            self.assertTrue(found_update, "UPDATE bikes query was executed")

if __name__ == "__main__":
    unittest.main()
