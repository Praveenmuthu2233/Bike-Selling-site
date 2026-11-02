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

print("\n------------------------------------------------------")
print(f"  TEST RESULTS: {passed} PASSED | {failed} FAILED")
print("------------------------------------------------------\n")

if failed > 0:
    sys.exit(1)
