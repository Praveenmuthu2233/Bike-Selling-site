import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_DIR = os.path.join(BASE_DIR, "my-node-app")
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import app

client = app.test_client()

# 1. Health check
res_h = client.get('/api/health')
print("HEALTH STATUS:", res_h.status_code)
h_data = res_h.get_json()
print("HEALTH DATA:", h_data)
assert res_h.status_code == 200, "Health endpoint should return 200 when connected"
assert h_data.get("status") == "healthy"
assert h_data.get("database", {}).get("status") == "connected"

# 2. Config endpoint
res_c = client.get('/api/config')
print("CONFIG STATUS:", res_c.status_code)
c_data = res_c.get_json()
print("CONFIG TIDB STATUS:", c_data.get("tidbStatus"))
print("CONFIG DATABASE METADATA:", c_data.get("database"))
assert c_data.get("tidbStatus") == "connected"
assert c_data.get("database", {}).get("targetDatabase") == "smr_motors"

# 3. Report alias endpoint test (without token -> 401 / 403, confirming route exists)
res_r1 = client.get('/api/admin/reports/bikes.pdf')
print("REPORTS PDF STATUS (no auth):", res_r1.status_code)
assert res_r1.status_code in (401, 403), "Route should exist and enforce auth"

res_r2 = client.get('/api/admin/reports/bikes.xlsx')
print("REPORTS XLSX STATUS (no auth):", res_r2.status_code)
assert res_r2.status_code in (401, 403), "Route should exist and enforce auth"

res_r3 = client.get('/api/admin/reports')
print("REPORTS ROOT STATUS (no auth):", res_r3.status_code)
assert res_r3.status_code in (401, 403), "Route should exist and enforce auth"

print("All health, config, and report route tests passed successfully!")
