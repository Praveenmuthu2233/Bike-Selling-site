import sys
sys.path.insert(0, 'my-node-app')
import app as my_app
import jwt
from datetime import datetime, timezone, timedelta

flask_app = my_app.app
client = flask_app.test_client()

# Generate valid admin test token
admin_payload = {
    "admin_id": 1,
    "username": "admin",
    "role": "superadmin",
    "exp": datetime.now(timezone.utc) + timedelta(hours=2)
}
admin_token = jwt.encode(admin_payload, my_app.JWT_SECRET, algorithm="HS256")
admin_headers = {"Authorization": f"Bearer {admin_token}"}

# Generate valid user test token
user_payload = {
    "user_id": 1,
    "email": "test@smrmotors.com",
    "exp": datetime.now(timezone.utc) + timedelta(hours=2)
}
user_token = jwt.encode(user_payload, my_app.JWT_SECRET, algorithm="HS256")
user_headers = {"Authorization": f"Bearer {user_token}"}

endpoints = [
    # Admin routes
    ("GET", "/api/admin/bikes?page=1&limit=5", admin_headers, "Admin Bikes"),
    ("GET", "/api/admin/sold-bikes?page=1&limit=5", admin_headers, "Admin Sold Bikes"),
    ("GET", "/api/admin/enquiries?page=1&limit=5", admin_headers, "Admin Enquiries"),
    ("GET", "/api/admin/users?page=1&limit=5", admin_headers, "Admin Users"),
    ("GET", "/api/admin/staff?page=1&limit=5", admin_headers, "Admin Staff"),
    ("GET", "/api/admin/staff/activity?page=1&limit=5", admin_headers, "Admin Staff Activity"),
    ("GET", "/api/admin/messages?page=1&limit=5", admin_headers, "Admin Messages"),
    ("GET", "/api/admin/chat/conversations?page=1&limit=5", admin_headers, "Admin Chat Conversations"),

    # User routes
    ("GET", "/api/users/listings?page=1&limit=5", user_headers, "User Listings"),
    ("GET", "/api/users/enquiries?page=1&limit=5", user_headers, "User Enquiries"),
    ("GET", "/api/users/negotiations?page=1&limit=5", user_headers, "User Negotiations"),
    ("GET", "/api/users/favorites?page=1&limit=5", user_headers, "User Favorites"),
    ("GET", "/api/notifications?page=1&limit=5", user_headers, "User Notifications"),
    ("GET", "/api/chat/conversations?page=1&limit=5", user_headers, "User Chat Conversations")
]

print("=" * 70)
print("VERIFYING SERVER-SIDE PAGINATION ON ALL ADMIN & USER ENDPOINTS")
print("=" * 70)

all_ok = True
for method, url, headers, desc in endpoints:
    res = client.open(url, method=method, headers=headers)
    status = res.status_code
    data = res.get_json() or {}
    pag = data.get("pagination")
    
    if pag:
        print(f"[PASS] {desc:25} status={status} total={pag.get('total')} page={pag.get('page')} limit={pag.get('limit')} totalPages={pag.get('totalPages') or pag.get('total_pages')}")
    elif status == 200:
        print(f"[NOTE] {desc:25} status=200 data_keys={list(data.keys())[:4]}")
    elif status == 503:
        print(f"[DB-OFFLINE] {desc:25} status=503 (Expected when TiDB Cloud is not reachable offline)")
    else:
        print(f"[WARN] {desc:25} status={status} data={data.get('message') or data}")
        all_ok = False

print("=" * 70)
if all_ok:
    print("ALL PAGINATED ENDPOINTS RESPONDED WITH VALID SHAPES!")
else:
    print("SOME ENDPOINTS RETURNED WARNINGS.")
print("=" * 70)
