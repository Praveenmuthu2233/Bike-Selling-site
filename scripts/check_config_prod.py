import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
url = 'https://bike-selling-site-lco8.onrender.com/api/config'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
    data = json.loads(resp.read().decode())
    print(json.dumps(data, indent=2))
