import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
url = 'https://bike-selling-site-lco8.onrender.com/api/admin/login'
payload = json.dumps({"username": "admin", "password": "wrongpassword"}).encode()
req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
        print("Status:", resp.status, resp.read().decode())
except urllib.error.HTTPError as e:
    print("HTTP error:", e.code, e.read().decode())
except Exception as e:
    print("Error:", e)
