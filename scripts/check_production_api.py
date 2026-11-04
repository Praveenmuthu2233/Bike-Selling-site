import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
url = 'https://bike-selling-site-lco8.onrender.com/api/bikes'
try:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=20, context=ctx) as resp:
        print('HTTP status:', resp.status)
        data = json.loads(resp.read().decode())
        print('Response data:', data)
except urllib.error.HTTPError as e:
    print('HTTP error:', e.code, e.read().decode())
except Exception as e:
    print('Error:', e)
