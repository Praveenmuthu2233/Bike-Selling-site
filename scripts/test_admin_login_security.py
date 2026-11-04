import sys
sys.path.insert(0, 'my-node-app')
import app as my_app

client = my_app.app.test_client()

print("=" * 70)
print("VERIFYING ADMIN LOGIN SECURITY & CREDENTIAL HYGIENE")
print("=" * 70)

# 1. Test GET /admin/login.html
res = client.get('/admin/login.html')
html = res.data.decode('utf-8')

assert 'value="admin"' not in html, "FAIL: value='admin' found in HTML!"
assert 'value="admin123"' not in html, "FAIL: value='admin123' found in HTML!"
assert 'placeholder="admin"' not in html, "FAIL: placeholder='admin' found in HTML!"
assert 'placeholder="Enter admin username"' in html, "FAIL: placeholder='Enter admin username' missing!"
assert 'placeholder="Enter admin password"' in html, "FAIL: placeholder='Enter admin password' missing!"
assert 'autocomplete="username"' in html, "FAIL: autocomplete='username' missing!"
assert 'autocomplete="current-password"' in html, "FAIL: autocomplete='current-password' missing!"

print("[PASS] GET /admin/login.html contains NO prepopulated credentials.")
print("[PASS] GET /admin/login.html enforces proper browser autocomplete attributes.")

# 2. Test fallback dictionary is empty
assert my_app.adminAccounts == {}, f"FAIL: adminAccounts is not empty: {my_app.adminAccounts}"
print("[PASS] Backend adminAccounts fallback dictionary is empty (no hardcoded passwords).")

# 3. Test POST /api/admin/login with invalid credentials
res_invalid = client.post('/api/admin/login', json={"username": "random_user", "password": "wrongpassword"})
assert res_invalid.status_code == 401, f"Expected 401, got {res_invalid.status_code}"
assert res_invalid.get_json().get("success") is False
print("[PASS] POST /api/admin/login with random credentials rejected with generic 401.")

# 4. Test POST /api/admin/login with empty credentials
res_empty = client.post('/api/admin/login', json={"username": "", "password": ""})
assert res_empty.status_code == 401, f"Expected 401, got {res_empty.status_code}"
assert res_empty.get_json().get("success") is False
print("[PASS] POST /api/admin/login with empty credentials rejected with generic 401.")

print("=" * 70)
print("ALL ADMIN LOGIN SECURITY & CREDENTIAL TESTS PASSED!")
print("=" * 70)
