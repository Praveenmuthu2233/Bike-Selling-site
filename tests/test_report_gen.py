import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'my-node-app'))

# Test report generation
from report_generator import generate_pdf_report, generate_excel_report

dummy_bikes = [
    {
        "id": 1,
        "title": "Yamaha MT-15 V2 Metallic Black",
        "brand": "Yamaha",
        "model": "MT-15 V2",
        "year": 2023,
        "price": 145000,
        "status": "approved",
        "listing_status": "published",
        "seller_name": "Praveen",
        "seller_phone": "+91 9876543210",
        "kilometers_driven": 12500,
        "fuel_type": "Petrol",
        "transmission": "Manual",
        "created_at": "2025-01-15 10:30:00"
    },
    {
        "id": 2,
        "title": "Royal Enfield Classic 350 Stealth",
        "brand": "Royal Enfield",
        "model": "Classic 350",
        "year": 2022,
        "price": 185000,
        "status": "pending",
        "listing_status": "pending",
        "seller_name": "Karthik",
        "seller_phone": "+91 9123456789",
        "kilometers_driven": 8500,
        "fuel_type": "Petrol",
        "transmission": "Manual",
        "created_at": "2025-02-01 14:20:00"
    }
]

filters = {"preset": "last_30_days", "status": "all", "brand": "all"}

print("Testing PDF Inventory Report generation...")
pdf_bytes = generate_pdf_report("listings", dummy_bikes, filters, generated_by="Superadmin Test", is_superadmin=True)
print(f"Generated PDF bytes: {len(pdf_bytes)}")
assert len(pdf_bytes) > 1000, "PDF bytes should be non-empty"

print("Testing Excel Inventory Report generation...")
xlsx_bytes = generate_excel_report("listings", dummy_bikes, filters, generated_by="Superadmin Test", is_superadmin=True)
print(f"Generated XLSX bytes: {len(xlsx_bytes)}")
assert len(xlsx_bytes) > 1000, "XLSX bytes should be non-empty"

dummy_txs = [
    {
        "id": 101,
        "bike_id": 1,
        "bike_title": "Yamaha MT-15 V2",
        "brand": "Yamaha",
        "year": 2023,
        "actual_sale_price": 145000,
        "seller_payout": 128000,
        "service_expense": 2500,
        "repair_expense": 1500,
        "total_expenses": 4000,
        "realized_profit": 13000,
        "buyer_name": "Anand R",
        "buyer_phone": "+91 9988776655",
        "seller_name": "Praveen",
        "seller_phone": "+91 9876543210",
        "sold_at": "2025-02-10 16:45:00",
        "notes": "Full service completed before handover"
    }
]

print("Testing Superadmin Financial PDF generation...")
fin_pdf = generate_pdf_report("financial", dummy_txs, filters, generated_by="Murugan (Owner)", is_superadmin=True)
print(f"Generated Financial PDF bytes: {len(fin_pdf)}")
assert len(fin_pdf) > 1000

print("Testing Superadmin Financial Excel generation...")
fin_xlsx = generate_excel_report("financial", dummy_txs, filters, generated_by="Murugan (Owner)", is_superadmin=True)
print(f"Generated Financial XLSX bytes: {len(fin_xlsx)}")
assert len(fin_xlsx) > 1000

print("Testing RBAC: Staff Admin trying to access financial report...")
try:
    generate_pdf_report("financial", dummy_txs, filters, generated_by="Mani (Staff)", is_superadmin=False)
    raise AssertionError("Staff admin should have been blocked!")
except PermissionError as e:
    print("RBAC block passed successfully:", e)

print("All report generator tests passed with flying colors!")
