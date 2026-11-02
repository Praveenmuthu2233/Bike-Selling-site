import sys
import os

# Add my-node-app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "my-node-app"))

import app

client = app.app.test_client()

passed = 0
failed = 0

def test(name, condition, details=""):
    global passed, failed
    if condition:
        print(f"  [PASS] {name}")
        passed += 1
    else:
        print(f"  [FAIL] {name} - {details}")
        failed += 1

print("\n======================================================")
print("  STARTING FLASK / RENDER INTEGRATION TEST SUITE")
print("======================================================\n")

# 1. Test Static CSS and JS assets return HTTP 200
for asset in [
    "/static/style.css",
    "/static/components.css",
    "/static/responsive.css",
    "/static/auth.css",
    "/static/user.css",
    "/static/adminStyle.css",
    "/static/config.js",
    "/static/api.js",
    "/static/auth.js",
    "/static/marketplace.js",
    "/static/main.js"
]:
    res = client.get(asset)
    test(f"Static Asset {asset} returns 200", res.status_code == 200, f"Status: {res.status_code}")

# 2. Test All 10 Templates Render with 200 and have CSS linked
templates_to_test = [
    ("/", "index.html"),
    ("/index.html", "index.html"),
    ("/userLogin.html", "userLogin.html"),
    ("/login", "userLogin.html"),
    ("/profile.html", "profile.html"),
    ("/admin.html", "admin.html"),
    ("/admin", "admin.html"),
    ("/adminAddListing.html", "adminAddListing.html"),
    ("/bikeSelling.html", "bikeSelling.html"),
    ("/enquiryBike.html", "enquiryBike.html"),
    ("/enquiry-bike-details.html", "enquiry-bike-details.html"),
    ("/listingUserBike.html", "listingUserBike.html"),
    ("/SoldOutPage.html", "SoldOutPage.html"),
    ("/about.html", "about.html"),
    ("/contact.html", "contact.html"),
]

for route, tmpl in templates_to_test:
    res = client.get(route)
    html = res.data.decode("utf-8")
    has_css = "stylesheet" in html and ("style.css" in html or "adminStyle.css" in html)
    test(f"Flask Route '{route}' renders {tmpl} (HTTP 200 & Stylesheet Linked)", res.status_code == 200 and has_css, f"Status: {res.status_code}, Has CSS: {has_css}")

# 3. Test API Endpoints
res_config = client.get("/api/config")
test("API GET /api/config returns 200 with googleClientId", res_config.status_code == 200 and "googleClientId" in res_config.json)

res_bikes = client.get("/api/bikes")
test("API GET /api/bikes returns 200 with inventory", res_bikes.status_code == 200 and len(res_bikes.json.get("bikes", [])) > 0)

res_legacy_bikes = client.get("/bikes")
test("API GET /bikes (legacy) returns 200", res_legacy_bikes.status_code == 200)

res_cats = client.get("/api/categories")
test("API GET /api/categories returns 200", res_cats.status_code == 200 and len(res_cats.json.get("categories", [])) > 0)

# Google OAuth Tests
res_auth_missing = client.post("/api/auth/google", json={})
test("API POST /api/auth/google rejects missing credential (HTTP 400)", res_auth_missing.status_code == 400)

res_auth_invalid = client.post("/api/auth/google", json={"credential": "invalid-malformed-token-12345"})
test("API POST /api/auth/google rejects invalid credential (HTTP 401)", res_auth_invalid.status_code == 401)

res_auth_mock = client.post("/api/auth/google", json={"credential": "test-mock-token-rider"})
test("API POST /api/auth/google validates verified token and returns JWT", res_auth_mock.status_code == 200 and "token" in res_auth_mock.json and res_auth_mock.json.get("user", {}).get("role") == "user")

res_auth = client.post("/api/auth/demo-google")
test("API POST /api/auth/demo-google returns 200 with JWT token", res_auth.status_code == 200 and "token" in res_auth.json)

token = res_auth.json.get("token")
res_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
test("API GET /api/auth/me returns authenticated user", res_me.status_code == 200 and res_me.json.get("success") == True)

res_me_no_auth = client.get("/api/auth/me")
test("API GET /api/auth/me rejects missing token (HTTP 401)", res_me_no_auth.status_code == 401)

res_me_bad_token = client.get("/api/auth/me", headers={"Authorization": "Bearer bad-token"})
test("API GET /api/auth/me rejects invalid token (HTTP 401)", res_me_bad_token.status_code == 401)

res_logout = client.post("/api/auth/logout")
test("API POST /api/auth/logout signs out cleanly (HTTP 200)", res_logout.status_code == 200)

res_admin_login = client.post("/api/admin/login", json={"username": "admin", "password": "admin123"})
test("API POST /api/admin/login validates credentials", res_admin_login.status_code == 200 and "token" in res_admin_login.json)

res_admin_dash = client.get("/api/admin/dashboard")
test("API GET /api/admin/dashboard returns telemetry metrics", res_admin_dash.status_code == 200 and "counts" in res_admin_dash.json.get("data", {}))

res_user_dash = client.get("/api/users/dashboard")
test("API GET /api/users/dashboard returns user metrics", res_user_dash.status_code == 200 and "stats" in res_user_dash.json.get("data", {}))

res_enquiry = client.post("/api/enquiries", json={"name": "Test Customer", "phone": "9876543210", "message": "Test enquiry"})
test("API POST /api/enquiries submits customer enquiry", res_enquiry.status_code == 201 and res_enquiry.json.get("success") == True)

res_contact = client.post("/api/contact", json={"name": "Test Contact", "email": "test@example.com", "message": "Test contact message"})
test("API POST /api/contact submits contact message", res_contact.status_code == 200 and res_contact.json.get("success") == True)

# 4. Scenario 1: Admin Login Page Loads Cleanly Without Redirect Loop
res_admin_login_page = client.get("/admin/login.html")
test("Admin Login Page /admin/login.html renders 200 without redirect", res_admin_login_page.status_code == 200 and "Admin Portal" in res_admin_login_page.data.decode("utf-8"))

res_admin_login_page_alt = client.get("/admin/login")
test("Admin Login Page /admin/login renders 200 without redirect", res_admin_login_page_alt.status_code == 200)

# 5. Scenario 2: Server-Side Pagination on GET /api/bikes (Desktop 9/page and Mobile 6/page)
res_bikes_p9 = client.get("/api/bikes?page=1&limit=9")
p9_json = res_bikes_p9.json
test("GET /api/bikes returns pagination object", res_bikes_p9.status_code == 200 and "pagination" in p9_json)
test("GET /api/bikes limit=9 sets pagination limit 9", p9_json.get("pagination", {}).get("limit") == 9)

res_bikes_p6 = client.get("/api/bikes?page=1&limit=6")
p6_json = res_bikes_p6.json
test("GET /api/bikes limit=6 sets pagination limit 6", p6_json.get("pagination", {}).get("limit") == 6)

# 6. Scenario 3: Price Negotiation Workflow (Propose -> Accept -> Publish -> Margin)
# 6a. Admin proposes seller payout
res_prop = client.post("/api/admin/bikes/1/propose-price", json={"proposed_payout": 135000, "message": "Fair market offer"})
test("POST /api/admin/bikes/1/propose-price succeeds", res_prop.status_code == 200 and res_prop.json.get("proposed_seller_payout") == 135000)

# 6b. Seller accepts payout offer
res_acc = client.post("/api/users/bikes/1/negotiate", json={"action": "accept", "message": "Agreed with offer"})
test("POST /api/users/bikes/1/negotiate (accept) succeeds", res_acc.status_code == 200 and res_acc.json.get("action") == "accept")

# 6c. Admin publishes bike with public price and calculates business margin
res_pub = client.post("/api/admin/bikes/1/publish", json={"public_selling_price": 148000})
pub_json = res_pub.json
test("POST /api/admin/bikes/1/publish sets public price and calculates margin", res_pub.status_code == 200 and pub_json.get("business_margin") == 13000)

# 7. Scenario 4: Mark Sold with Expense Breakdown & Net Realized Profit
res_sold = client.post("/api/admin/bikes/1/mark-sold", json={
    "actual_sale_price": 146000,
    "seller_payout": 135000,
    "service_expense": 2000,
    "repair_expense": 1000,
    "transport_expense": 500,
    "other_expense": 500,
    "notes": "Delivered with RC endorsement",
    "buyer_name": "Karthik Raja"
})
sold_json = res_sold.json
tx = sold_json.get("transaction", {})
# Realized profit = 146000 - 135000 - 4000 = 7000
test("POST /api/admin/bikes/1/mark-sold calculates realized profit", res_sold.status_code == 200 and tx.get("realized_profit") == 7000)
test("Total expenses correctly calculated", tx.get("total_expenses") == 4000)

# 8. Scenario 5: Public Sold Gallery Sanitization (No private payout/profit leaked)
res_pub_sold = client.get("/api/bikes/sold")
pub_sold_json = res_pub_sold.json
sold_items = pub_sold_json.get("bikes", [])
test("GET /api/bikes/sold returns 200 with sold bikes", res_pub_sold.status_code == 200 and len(sold_items) > 0)
leaks_found = any("seller_payout" in item or "realized_profit" in item for item in sold_items)
test("GET /api/bikes/sold DOES NOT leak seller payout or realized profit", not leaks_found)

# 9. Scenario 6: Admin Data Exports (CSV & Excel)
res_exp_bikes_csv = client.get("/api/admin/export/bikes?format=csv")
test("GET /api/admin/export/bikes format=csv returns CSV file", res_exp_bikes_csv.status_code == 200 and "text/csv" in res_exp_bikes_csv.content_type)

res_exp_bikes_xlsx = client.get("/api/admin/export/bikes?format=xlsx")
test("GET /api/admin/export/bikes format=xlsx returns Excel file", res_exp_bikes_xlsx.status_code == 200 and "spreadsheetml" in res_exp_bikes_xlsx.content_type)

res_exp_sold_csv = client.get("/api/admin/export/sold?format=csv")
sold_csv_text = res_exp_sold_csv.data.decode("utf-8-sig")
test("GET /api/admin/export/sold returns CSV with exact financial columns", res_exp_sold_csv.status_code == 200 and "Realized Net Profit" in sold_csv_text and "TOTALS" in sold_csv_text)

# 10. Scenario 7: Notifications API
res_notifs = client.get("/api/notifications")
test("GET /api/notifications returns list and unread count", res_notifs.status_code == 200 and "notifications" in res_notifs.json)

res_mark_read = client.put("/api/notifications/read-all")
test("PUT /api/notifications/read-all marks all read", res_mark_read.status_code == 200)

# 11. Scenario 8: Admin Financial Analytics & Telemetry
res_dash_fin = client.get("/api/admin/dashboard")
dash_fin_json = res_dash_fin.json.get("data", {})
counts = dash_fin_json.get("counts", {})
test("Admin Dashboard includes total revenue calculation", counts.get("total_revenue", 0) > 0)
test("Admin Dashboard includes realized profit calculation", counts.get("total_realized_profit", 0) > 0)
test("Admin Dashboard includes monthly trends", len(dash_fin_json.get("financials", {}).get("monthly_trends", [])) > 0)

print("\n------------------------------------------------------")
print(f"  TEST RESULTS: {passed} PASSED | {failed} FAILED")
print("------------------------------------------------------\n")

if failed > 0:
    sys.exit(1)
