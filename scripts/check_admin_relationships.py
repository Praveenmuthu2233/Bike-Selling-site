import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
# Login as admin to get token
url = 'https://bike-selling-site-lco8.onrender.com/api/admin/login'
payload = json.dumps({"username": "admin", "password": "admin123"}).encode()
req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
    token = json.loads(resp.read().decode())['token']

headers = {'Authorization': f'Bearer {token}', 'User-Agent': 'Mozilla/5.0'}

# 1. Check chat conversations assigned to admin ID 1
chat_req = urllib.request.Request('https://bike-selling-site-lco8.onrender.com/api/admin/chat/conversations?limit=100', headers=headers)
with urllib.request.urlopen(chat_req, timeout=15, context=ctx) as resp:
    c_data = json.loads(resp.read().decode())
    convs = c_data.get('conversations', [])
    assigned_convs = [c for c in convs if c.get('assigned_admin_id') == 1]
    print(f"Chat conversations assigned to admin ID 1: {len(assigned_convs)} of {len(convs)}")

# 2. Check audit logs for admin
audit_req = urllib.request.Request('https://bike-selling-site-lco8.onrender.com/api/admin/staff/activity?limit=100', headers=headers)
with urllib.request.urlopen(audit_req, timeout=15, context=ctx) as resp:
    a_data = json.loads(resp.read().decode())
    logs = a_data.get('data', [])
    admin_logs = [l for l in logs if l.get('admin_username') == 'admin' or l.get('admin_id') == 1]
    print(f"Audit logs by admin ID 1: {len(admin_logs)} of {len(logs)}")

# 3. Check sold bikes
sold_req = urllib.request.Request('https://bike-selling-site-lco8.onrender.com/api/admin/sold-bikes?limit=100', headers=headers)
with urllib.request.urlopen(sold_req, timeout=15, context=ctx) as resp:
    s_data = json.loads(resp.read().decode())
    sold = s_data.get('data', [])
    sold_by_admin = [b for b in sold if b.get('sold_by') == 'admin']
    print(f"Sold bikes handled by admin: {len(sold_by_admin)} of {len(sold)}")
