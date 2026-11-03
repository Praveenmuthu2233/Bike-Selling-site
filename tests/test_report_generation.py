import sys
import os
import unittest
import zipfile
import io

sys.path.append('my-node-app')
from report_generator import generate_pdf_report, generate_excel_report, REPORTLAB_AVAILABLE, OPENPYXL_AVAILABLE

class TestReportGeneration(unittest.TestCase):
    def setUp(self):
        self.sample_items = [
            {
                "id": 101,
                "bike_id": 101,
                "title": "Royal Enfield Classic 350 Stealth Black",
                "brand": "Royal Enfield",
                "model": "Classic 350",
                "year": 2023,
                "price": 195000,
                "requested_price": 190000,
                "kilometers_driven": 6200,
                "fuel_type": "Petrol",
                "transmission": "Manual",
                "seller_name": "SMR Motors",
                "seller_phone": "+91 98765 43210",
                "registration_number": "TN-01-AB-1234",
                "status": "approved",
                "listing_status": "published",
                "created_at": "2026-01-10",
                "sold_at": "2026-02-15",
                "sold_by": "admin",
                "actual_sale_price": 192000,
                "seller_payout": 178000,
                "service_expense": 2000,
                "repair_expense": 1500,
                "transport_expense": 1000,
                "other_expense": 500,
                "total_expenses": 5000,
                "realized_profit": 9000
            },
            {
                "id": 102,
                "bike_id": 102,
                "title": "Yamaha MT-15 V2 Cyber Green",
                "brand": "Yamaha",
                "model": "MT-15 V2",
                "year": 2022,
                "price": 138000,
                "requested_price": 135000,
                "kilometers_driven": 14500,
                "fuel_type": "Petrol",
                "transmission": "Manual",
                "seller_name": "Karthik Raja",
                "seller_phone": "+91 94444 33333",
                "registration_number": "TN-02-CD-5678",
                "status": "soldout",
                "listing_status": "soldout",
                "created_at": "2026-01-15",
                "sold_at": "2026-02-20",
                "sold_by": "staffadmin",
                "actual_sale_price": 136000,
                "seller_payout": 125000,
                "service_expense": 1500,
                "repair_expense": 500,
                "transport_expense": 500,
                "other_expense": 500,
                "total_expenses": 3000,
                "realized_profit": 8000
            }
        ]
        self.filters = {"status": "all", "brand": "all"}

    def test_reportlab_engine_available(self):
        """Verify reportlab is installed and flagged available."""
        self.assertTrue(REPORTLAB_AVAILABLE, "ReportLab must be installed and available")

    def test_openpyxl_engine_available(self):
        """Verify openpyxl is installed and flagged available."""
        self.assertTrue(OPENPYXL_AVAILABLE, "openpyxl must be installed and available")

    def test_generate_pdf_listings(self):
        """Verify listings PDF generation."""
        pdf_bytes = generate_pdf_report("listings", self.sample_items, self.filters, "Administrator", False)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(len(pdf_bytes) > 1000, "PDF bytes should be substantial")
        self.assertTrue(pdf_bytes.startswith(b"%PDF"), "PDF file must start with %PDF header")

    def test_generate_pdf_sold(self):
        """Verify sold motorcycles PDF generation."""
        pdf_bytes = generate_pdf_report("sold", self.sample_items, self.filters, "Administrator", False)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(len(pdf_bytes) > 1000)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_generate_pdf_financials_superadmin(self):
        """Verify superadmin financial telemetry PDF generation."""
        pdf_bytes = generate_pdf_report("financial", self.sample_items, self.filters, "Superadmin", True)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(len(pdf_bytes) > 1000)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_generate_pdf_financials_forbidden_for_staff(self):
        """Verify RBAC: non-superadmin cannot generate financial PDF."""
        with self.assertRaises(PermissionError):
            generate_pdf_report("financial", self.sample_items, self.filters, "StaffAdmin", False)

    def test_generate_excel_listings(self):
        """Verify listings Excel report generation."""
        xlsx_bytes = generate_excel_report("listings", self.sample_items, self.filters, "Administrator", False)
        self.assertIsInstance(xlsx_bytes, bytes)
        self.assertTrue(len(xlsx_bytes) > 1000)
        # Verify valid zip/xlsx archive
        zf = zipfile.ZipFile(io.BytesIO(xlsx_bytes))
        self.assertIn("[Content_Types].xml", zf.namelist())

    def test_generate_excel_sold(self):
        """Verify sold motorcycles Excel report generation."""
        xlsx_bytes = generate_excel_report("sold", self.sample_items, self.filters, "Administrator", False)
        self.assertIsInstance(xlsx_bytes, bytes)
        self.assertTrue(len(xlsx_bytes) > 1000)
        zf = zipfile.ZipFile(io.BytesIO(xlsx_bytes))
        self.assertIn("[Content_Types].xml", zf.namelist())

    def test_generate_excel_financials_superadmin(self):
        """Verify superadmin financial telemetry Excel generation."""
        xlsx_bytes = generate_excel_report("financial", self.sample_items, self.filters, "Superadmin", True)
        self.assertIsInstance(xlsx_bytes, bytes)
        self.assertTrue(len(xlsx_bytes) > 1000)
        zf = zipfile.ZipFile(io.BytesIO(xlsx_bytes))
        self.assertIn("[Content_Types].xml", zf.namelist())

    def test_generate_excel_financials_forbidden_for_staff(self):
        """Verify RBAC: non-superadmin cannot generate financial Excel."""
        with self.assertRaises(PermissionError):
            generate_excel_report("financial", self.sample_items, self.filters, "StaffAdmin", False)

if __name__ == '__main__':
    unittest.main()
