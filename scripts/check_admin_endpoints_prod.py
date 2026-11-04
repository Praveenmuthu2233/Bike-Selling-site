import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwidXNlcm5hbWUiOiJhZG1pbiIsIm5hbWUiOiJBZG1pbmlzdHJhdG9yIiwicm9sZSI6InN1cGVyYWRtaW4iLCJleHAiOjE3OTQzNzE2MTh9.swhK5wvrRma6tKdjzdw8pUPaFH0oU3fLcnmwv_HMy0Y"

for ep in ['/api/admin/dashboard', '/api/admin/bikes?tab=pending', '/api/admin/staff']:
    url = f'https://bike-selling-site-lco8.onrender.com{ep}'
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}', 'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            print(f"{ep}: {resp.status} -> {resp.read().decode()[:150]}")
    except urllib.error.HTTPError as e:
        print(f"{ep}: HTTP {e.code} -> {e.read().decode()[:150]}")
    except Exception as e:
        print(f"{ep}: Error -> {e}")
