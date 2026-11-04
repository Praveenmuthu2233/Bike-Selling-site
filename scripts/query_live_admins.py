import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
# First login to get a fresh token
url = 'https://bike-selling-site-lco8.onrender.com/api/admin/login'
payload = json.dumps({"username": "admin", "password": "admin123"}).encode()
req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
    data = json.loads(resp.read().decode())
    token = data['token']
    print("Admin info from login:", data.get('admin'))

# Now query /api/admin/staff
staff_url = 'https://bike-selling-site-lco8.onrender.com/api/admin/staff'
s_req = urllib.request.Request(staff_url, headers={'Authorization': f'Bearer {token}', 'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(s_req, timeout=15, context=ctx) as resp:
    staff_data = json.loads(resp.read().decode())
    print("\nStaff members in live database:")
    print(json.dumps(staff_data, indent=2))
